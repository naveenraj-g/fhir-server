"""Core questionnaire response endpoint coverage.

QuestionnaireResponse is stored whole in `content` (like CareTeam, CarePlan, Encounter and the
other content-based resources): the request body (genuine FHIR R4 QuestionnaireResponse JSON) is
validated and stored in `content`, every response is FHIR R4 (`application/fhir+json`, regardless
of Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/questionnaireresponse.html#search) - R4 has none for the answers, so
the whole `item` tree is plain content.

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`subject`, `encounter`, `author`,
`source`, `basedOn`, `partOf`, an answer's `valueReference` at any depth and every identifier's
`assigner`). Search lives in test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.questionnaire_response.conftest import RESPONSE_PERMS
from tests.integration.questionnaire_response.support import (
    BASE,
    QUESTIONNAIRE,
    care_plan_body,
    create_care_plan,
    create_encounter,
    create_group,
    create_observation,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_procedure,
    create_questionnaire_response,
    create_related_person,
    create_service_request,
    encounter_body,
    full_body,
    group_body,
    observation_body,
    procedure_body,
    questionnaire_response_body,
    related_person_body,
    service_request_body,
)


@pytest.fixture
def native_validation(monkeypatch):
    """The base R4 validator may be switched off in configs/config.yaml (`fhir_validation.enabled:
    false` skips it entirely). Tests that assert "a key that isn't FHIR is a 422" need it on: the
    project's own structural check (no sidecar needed)."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=RESPONSE_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    organization = await create_organization(client)
    patient = await create_patient(client)
    practitioner = await create_practitioner(client)
    encounter = await create_encounter(client, encounter_body())
    care_plan = await create_care_plan(client, care_plan_body(patient))
    observation = await create_observation(client, observation_body(patient))
    body = full_body(
        organization, patient, practitioner, encounter, care_plan, observation
    )
    return await create_questionnaire_response(client, body), body


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=questionnaire_response_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    assert resp.json()["resourceType"] == "QuestionnaireResponse"
    assert resp.json()["id"] == "60000"  # the first id of the block


async def test_create_full_round_trip_including_the_whole_item_tree(client):
    response, body = await _full(client)
    data = (await client.get(f"{BASE}/{response}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_the_nested_tree_in_order(client):
    """item.item and answer.item nest to any depth and keep their order, and every value[x]."""
    response, body = await _full(client)
    data = (await client.get(f"{BASE}/{response}")).json()
    assert [i["linkId"] for i in data["item"]] == ["1", "2"]
    nested = data["item"][0]["item"][1]["answer"][0]["item"][0]
    assert nested["linkId"] == "1.2.1"
    assert nested["answer"][0]["valueQuantity"]["comparator"] == ">"
    assert nested["answer"][0]["valueQuantity"]["value"] == 72.5
    kinds = [next(iter(a)) for a in data["item"][1]["answer"]]
    assert kinds == [
        "valueBoolean",
        "valueDecimal",
        "valueDate",
        "valueDateTime",
        "valueTime",
        "valueString",
        "valueUri",
        "valueAttachment",
    ]


async def test_create_deeply_nested_items(client):
    item = {"linkId": "leaf", "answer": [{"valueString": "x"}]}
    for depth in range(12):
        item = {"linkId": f"g{depth}", "item": [item]}
    body = questionnaire_response_body(item=[item])
    response = await create_questionnaire_response(client, body)
    data = (await client.get(f"{BASE}/{response}")).json()
    node = data["item"][0]
    for depth in range(11, -1, -1):
        assert node["linkId"] == f"g{depth}"
        node = node["item"][0]
    assert node == {"linkId": "leaf", "answer": [{"valueString": "x"}]}


@pytest.mark.parametrize(
    "status", ["in-progress", "completed", "amended", "entered-in-error", "stopped"]
)
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(
        BASE + "/", json=questionnaire_response_body(status=status)
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_ignores_server_managed_id_and_meta(client):
    body = questionnaire_response_body(
        id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "retired"},
        {"status": "in_progress"},
        {"identifier": [{"value": "x"}]},
        {"basedOn": {"reference": "CarePlan/1"}},
        {"basedOn": ["CarePlan/1"]},
        {"partOf": {"reference": "Observation/1"}},
        {"questionnaire": {"reference": "Questionnaire/1"}},
        {"subject": "Patient/1"},
        {"encounter": "Encounter/1"},
        {"authored": 5},
        {"author": [{"reference": "Practitioner/1"}]},
        {"source": "Patient/1"},
        {"item": {"linkId": "1"}},
        {"item": ["x"]},
        {"item": [{"linkId": 1}]},
        {"item": [{"linkId": "1", "answer": {"valueString": "x"}}]},
        {"item": [{"linkId": "1", "answer": [{"valueInteger": "two"}]}]},
        {"item": [{"linkId": "1", "answer": [{"valueBoolean": "yes"}]}]},
        {"item": [{"linkId": "1", "answer": [{"valueCoding": "x"}]}]},
        {"item": [{"linkId": "1", "answer": [{"item": {"linkId": "2"}}]}]},
        {"item": [{"linkId": "1", "item": [{"linkId": "2", "item": "x"}]}]},
    ):
        resp = await client.post(BASE + "/", json=questionnaire_response_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(
        BASE + "/", json=questionnaire_response_body(not_a_fhir_element=1)
    )
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in (
        {"subject_id": 1},
        {"org_id": "x"},
        {"user_id": "x"},
        {"identifier_value": "x"},
    ):
        resp = await client.post(
            BASE + "/", json={**questionnaire_response_body(), **stale}
        )
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(
        BASE + "/", json=questionnaire_response_body(resourceType="Patient")
    )
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=questionnaire_response_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_subject_may_be_any_resource_but_must_exist(client):
    patient = await create_patient(client)
    group = await create_group(client, group_body(type="person"))
    observation = await create_observation(client, observation_body(patient))
    for ref in (f"Patient/{patient}", f"Group/{group}", f"Observation/{observation}"):
        body = questionnaire_response_body(subject={"reference": ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for ref in ("Patient/999999", "Group/999999", "Observation/999999"):
        body = questionnaire_response_body(subject={"reference": ref})
        resp = await client.post(BASE + "/", json=body)
        assert resp.status_code == 422 and "subject" in resp.text, ref


async def test_create_encounter_must_exist(client):
    encounter = await create_encounter(client, encounter_body())
    ok = questionnaire_response_body(encounter={"reference": f"Encounter/{encounter}"})
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = questionnaire_response_body(encounter={"reference": "Encounter/999999"})
    resp = await client.post(BASE + "/", json=bad)
    assert resp.status_code == 422 and "encounter" in resp.text


async def test_create_author_and_source_must_exist(client):
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    patient = await create_patient(client)
    related = await create_related_person(client, related_person_body(patient))
    role = await create_practitioner_role(
        client, {"practitioner": {"reference": f"Practitioner/{practitioner}"}}
    )
    for ref in (
        f"Practitioner/{practitioner}",
        f"PractitionerRole/{role}",
        f"Organization/{organization}",
        f"Patient/{patient}",
        f"RelatedPerson/{related}",
    ):
        body = questionnaire_response_body(author={"reference": ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for ref in (
        f"Patient/{patient}",
        f"RelatedPerson/{related}",
        f"PractitionerRole/{role}",
    ):
        body = questionnaire_response_body(source={"reference": ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for element in ("author", "source"):
        bad = questionnaire_response_body(
            **{element: {"reference": "Practitioner/999999"}}
        )
        resp = await client.post(BASE + "/", json=bad)
        assert resp.status_code == 422 and element in resp.text, element


async def test_create_based_on_and_part_of_must_exist(client):
    patient = await create_patient(client)
    care_plan = await create_care_plan(client, care_plan_body(patient))
    request = await create_service_request(client, service_request_body(patient))
    observation = await create_observation(client, observation_body(patient))
    procedure = await create_procedure(client, procedure_body(patient))
    ok = questionnaire_response_body(
        basedOn=[
            {"reference": f"CarePlan/{care_plan}"},
            {"reference": f"ServiceRequest/{request}"},
        ],
        partOf=[
            {"reference": f"Observation/{observation}"},
            {"reference": f"Procedure/{procedure}"},
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for element, ref in (
        ("basedOn", "CarePlan/999999"),
        ("basedOn", "ServiceRequest/999999"),
        ("partOf", "Observation/999999"),
        ("partOf", "Procedure/999999"),
    ):
        resp = await client.post(
            BASE + "/",
            json=questionnaire_response_body(**{element: [{"reference": ref}]}),
        )
        assert resp.status_code == 422 and f"{element}[0]" in resp.text, (element, ref)


async def test_create_answer_references_are_checked_at_any_depth(client):
    patient = await create_patient(client)
    ok_target = await create_observation(client, observation_body(patient))

    def nested(reference):
        return questionnaire_response_body(
            item=[
                {
                    "linkId": "1",
                    "item": [
                        {
                            "linkId": "1.1",
                            "answer": [
                                {
                                    "valueString": "x",
                                    "item": [
                                        {
                                            "linkId": "1.1.1",
                                            "answer": [
                                                {
                                                    "valueReference": {
                                                        "reference": reference
                                                    }
                                                }
                                            ],
                                        }
                                    ],
                                }
                            ],
                        }
                    ],
                }
            ]
        )

    assert (
        await client.post(BASE + "/", json=nested(f"Observation/{ok_target}"))
    ).status_code == 201
    resp = await client.post(BASE + "/", json=nested("Observation/999999"))
    assert resp.status_code == 422
    assert (
        "valueReference" in resp.text
        and "item[0].item[0].answer[0].item[0]" in resp.text
    )


async def test_create_every_identifier_assigner_must_exist(client):
    bad = questionnaire_response_body(
        identifier={"value": "1", "assigner": {"reference": "Organization/999999"}}
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    body = questionnaire_response_body(subject={"reference": f"Patient/{theirs}"})
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_absolute_logical_and_unmodeled_references_not_resolved(client):
    """An absolute URL, a logical (identifier-only) reference, a Device (not a resource on this
    server) and a canonical `questionnaire` are stored as sent."""
    body = questionnaire_response_body(
        subject={"reference": "https://other.example.org/fhir/Patient/1"},
        author={"reference": "Device/12"},
        source={"identifier": {"system": "urn:pr", "value": "P-9"}},
        basedOn=[{"reference": "https://other.example.org/fhir/CarePlan/9"}],
        questionnaire="Questionnaire/999999",
        item=[
            {
                "linkId": "1",
                "answer": [
                    {
                        "valueReference": {
                            "reference": "https://other.example.org/Thing/1"
                        }
                    }
                ],
            }
        ],
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["subject"]["reference"] == "https://other.example.org/fhir/Patient/1"
    assert data["author"]["reference"] == "Device/12"
    assert data["source"]["identifier"]["value"] == "P-9"
    assert data["questionnaire"] == "Questionnaire/999999"


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    response, _ = await _full(client)
    resp = await client.get(f"{BASE}/{response}")
    assert resp.status_code == 200 and resp.json()["id"] == str(response)


async def test_get_is_fhir_regardless_of_accept(client):
    response = await create_questionnaire_response(
        client, questionnaire_response_body()
    )
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{response}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "QuestionnaireResponse"


async def test_xml_only_accept_is_406(client):
    response = await create_questionnaire_response(
        client, questionnaire_response_body()
    )
    resp = await client.get(
        f"{BASE}/{response}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    response, body = await _full(client)
    resp = await client.patch(f"{BASE}/{response}", json={"status": "amended"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "amended"
    assert resp.json()["item"] == body["item"]  # untouched
    assert resp.json()["questionnaire"] == body["questionnaire"]


async def test_patch_reindexes_search(client):
    response, _ = await _full(client)
    patient = await create_patient(client)
    await client.patch(
        f"{BASE}/{response}",
        json={
            "status": "stopped",
            "authored": "2030-05-06T07:08:09Z",
            "subject": {"reference": f"Patient/{patient}"},
            "questionnaire": "https://fhir-server.dev/fhir/Questionnaire/gad-7",
            "basedOn": [],
        },
    )
    for param, old, new in (
        ("status", "completed", "stopped"),
        ("authored", "2026", "2030"),
        (
            "questionnaire",
            QUESTIONNAIRE,
            "https://fhir-server.dev/fhir/Questionnaire/gad-7",
        ),
        ("patient", None, str(patient)),
    ):
        if old is not None:
            assert response not in _ids(
                (await client.get(BASE + "/", params={param: old})).json()
            ), param
        assert response in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param
    assert response in _ids(
        (await client.get(BASE + "/", params={"based-on:missing": "true"})).json()
    )


async def test_patch_replaces_the_whole_item_tree(client):
    response, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{response}",
        json={"item": [{"linkId": "only", "answer": [{"valueString": "new"}]}]},
    )
    assert resp.json()["item"] == [
        {"linkId": "only", "answer": [{"valueString": "new"}]}
    ]
    cleared = await client.patch(f"{BASE}/{response}", json={"item": []})
    assert "item" not in cleared.json()
    assert cleared.json()["status"] == "completed"  # untouched


async def test_patch_clears_subject_and_missing_follows(client):
    patient = await create_patient(client)
    response = await create_questionnaire_response(
        client, questionnaire_response_body(subject={"reference": f"Patient/{patient}"})
    )
    resp = await client.patch(f"{BASE}/{response}", json={"subject": None})
    assert "subject" not in resp.json()
    assert response in _ids(
        (await client.get(BASE + "/", params={"subject:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    response = await create_questionnaire_response(
        client, questionnaire_response_body()
    )
    resp = await client.patch(
        f"{BASE}/{response}",
        json={"author": {"reference": "Practitioner/999999"}},
    )
    assert resp.status_code == 422
    assert "author" not in (await client.get(f"{BASE}/{response}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    response = await create_questionnaire_response(
        client, questionnaire_response_body(status="completed")
    )
    assert (
        await client.patch(f"{BASE}/{response}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{response}")).json()["status"] == "completed"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "amended"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    response, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{response}")).status_code == 204
    assert (await client.get(f"{BASE}/{response}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "QR-1001"),
        ("status", "completed"),
        ("questionnaire", QUESTIONNAIRE),
    ):
        assert response not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["questionnaire_response:read"])
    assert (
        await client.post(BASE + "/", json=questionnaire_response_body())
    ).status_code == 403


async def test_org_less_token_rejected(client):
    response = await create_questionnaire_response(
        client, questionnaire_response_body()
    )

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": RESPONSE_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (
        await client.post(BASE + "/", json=questionnaire_response_body())
    ).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{response}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    response = await create_questionnaire_response(
        client, questionnaire_response_body()
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{response}"),
            await other_client.patch(f"{BASE}/{response}", json={"status": "amended"}),
            await other_client.delete(f"{BASE}/{response}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_questionnaire_response(
        client,
        questionnaire_response_body(
            identifier={"system": "urn:t", "value": "TenantAOnly"}
        ),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


# -- Other resources that point at a response ------------------------------------------------


async def test_response_is_checked_where_a_reference_any_can_name_it(client):
    """DetectedIssue.implicated is a Reference(Any): a relative QuestionnaireResponse there must
    exist."""
    response = await create_questionnaire_response(
        client, questionnaire_response_body()
    )
    issues = "/api/fhir/v1/detected-issues/"
    ok = {
        "status": "final",
        "implicated": [{"reference": f"QuestionnaireResponse/{response}"}],
    }
    assert (await client.post(issues, json=ok)).status_code == 201
    missing = {
        "status": "final",
        "implicated": [{"reference": "QuestionnaireResponse/999999"}],
    }
    assert (await client.post(issues, json=missing)).status_code == 422


async def test_response_is_checked_in_observation_derived_from_and_has_member(client):
    patient = await create_patient(client)
    response = await create_questionnaire_response(
        client, questionnaire_response_body()
    )
    observations = "/api/fhir/v1/observations/"
    for element in ("derivedFrom", "hasMember"):
        ok = observation_body(
            patient, **{element: [{"reference": f"QuestionnaireResponse/{response}"}]}
        )
        assert (await client.post(observations, json=ok)).status_code == 201, element
        missing = observation_body(
            patient, **{element: [{"reference": "QuestionnaireResponse/999999"}]}
        )
        assert (await client.post(observations, json=missing)).status_code == 422, (
            element
        )

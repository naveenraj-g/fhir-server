"""Core medication statement endpoint coverage.

MedicationStatement is stored whole in `content` (like MedicationRequest, QuestionnaireResponse
and the other content-based resources): the request body (genuine FHIR R4 MedicationStatement
JSON) is validated and stored in `content`, every response is FHIR R4 (`application/fhir+json`,
regardless of Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/medicationstatement.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`subject`, `context`,
`informationSource`, `medicationReference`, `partOf`, `reasonReference`, a note author and every
identifier's `assigner`). Search lives in test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.medication_statement.conftest import STATEMENT_PERMS
from tests.integration.medication_statement.support import (
    BASE,
    condition_body,
    create_condition,
    create_encounter,
    create_episode,
    create_group,
    create_medication,
    create_medication_statement,
    create_observation,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_procedure,
    create_related_person,
    encounter_body,
    episode_body,
    full_body,
    group_body,
    medication_body,
    medication_statement_body,
    observation_body,
    procedure_body,
    related_person_body,
)


@pytest.fixture
def native_validation(monkeypatch):
    """The base R4 validator may be switched off in configs/config.yaml; tests that assert "a key
    that isn't FHIR is a 422" need it on: the project's own structural check."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=STATEMENT_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client, with_medication_reference=False) -> tuple[int, dict]:
    organization = await create_organization(client)
    patient = await create_patient(client)
    practitioner = await create_practitioner(client)
    encounter = await create_encounter(client, encounter_body())
    observation = await create_observation(client, observation_body(patient))
    condition = await create_condition(client, condition_body(patient))
    medication = (
        await create_medication(client, medication_body())
        if with_medication_reference
        else None
    )
    body = full_body(
        organization,
        patient,
        practitioner,
        encounter,
        observation,
        condition,
        medication,
    )
    return await create_medication_statement(client, body), body


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=medication_statement_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    assert resp.json()["resourceType"] == "MedicationStatement"
    assert resp.json()["id"] == "500000"  # the first id of the block


async def test_create_full_round_trip_including_dosage_and_notes(client):
    statement, body = await _full(client)
    data = (await client.get(f"{BASE}/{statement}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_with_a_medication_reference(client):
    statement, body = await _full(client, with_medication_reference=True)
    data = (await client.get(f"{BASE}/{statement}")).json()
    assert data["medicationReference"] == body["medicationReference"]
    assert "medicationCodeableConcept" not in data


async def test_create_effective_date_time_and_period_round_trip(client):
    one = await create_medication_statement(
        client, medication_statement_body(effectiveDateTime="2026-02-03T08:30:00Z")
    )
    two = await create_medication_statement(
        client,
        medication_statement_body(
            effectivePeriod={"start": "2026-01-01", "end": "2026-02-01"}
        ),
    )
    assert (await client.get(f"{BASE}/{one}")).json()[
        "effectiveDateTime"
    ] == "2026-02-03T08:30:00Z"
    assert (await client.get(f"{BASE}/{two}")).json()["effectivePeriod"] == {
        "start": "2026-01-01",
        "end": "2026-02-01",
    }


@pytest.mark.parametrize(
    "status",
    [
        "active",
        "completed",
        "entered-in-error",
        "intended",
        "stopped",
        "on-hold",
        "unknown",
        "not-taken",
    ],
)
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=medication_statement_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_ignores_server_managed_id_and_meta(client):
    body = medication_statement_body(
        id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "bogus"},
        {"status": "entered_in_error"},
        {"identifier": {"value": "x"}},
        {"basedOn": {"reference": "CarePlan/1"}},
        {"basedOn": ["CarePlan/1"]},
        {"partOf": {"reference": "Observation/1"}},
        {"statusReason": {"text": "x"}},
        {"category": [{"text": "x"}]},
        {"subject": "Patient/1"},
        {"context": "Encounter/1"},
        {"effectiveDateTime": 5},
        {"effectivePeriod": "2026"},
        {"dateAsserted": 5},
        {"informationSource": [{"reference": "Practitioner/1"}]},
        {"derivedFrom": {"reference": "x"}},
        {"reasonCode": {"text": "x"}},
        {"reasonReference": {"reference": "Condition/1"}},
        {"note": {"text": "x"}},
        {"note": ["x"]},
        {"dosage": {"text": "x"}},
        {"dosage": ["x"]},
    ):
        resp = await client.post(BASE + "/", json=medication_statement_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(
        BASE + "/", json=medication_statement_body(not_a_fhir_element=1)
    )
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in (
        {"subject_id": 1},
        {"org_id": "x"},
        {"user_id": "x"},
        {"effective_date_time": "2026-01-01"},
        {"category_text": "x"},
    ):
        resp = await client.post(
            BASE + "/", json={**medication_statement_body(), **stale}
        )
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(
        BASE + "/", json=medication_statement_body(resourceType="Patient")
    )
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=medication_statement_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_subject_must_exist_patient_or_group(client):
    patient = await create_patient(client)
    group = await create_group(client, group_body(type="person"))
    for ref in (f"Patient/{patient}", f"Group/{group}"):
        body = medication_statement_body(subject={"reference": ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for ref in ("Patient/999999", "Group/999999"):
        body = medication_statement_body(subject={"reference": ref})
        resp = await client.post(BASE + "/", json=body)
        assert resp.status_code == 422 and "subject" in resp.text, ref


async def test_create_context_must_exist(client):
    encounter = await create_encounter(client, encounter_body())
    patient = await create_patient(client)
    episode = await create_episode(client, episode_body(patient))
    for ref in (f"Encounter/{encounter}", f"EpisodeOfCare/{episode}"):
        body = medication_statement_body(context={"reference": ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for ref in ("Encounter/999999", "EpisodeOfCare/999999"):
        body = medication_statement_body(context={"reference": ref})
        resp = await client.post(BASE + "/", json=body)
        assert resp.status_code == 422 and "context" in resp.text, ref


async def test_create_information_source_must_exist(client):
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
        body = medication_statement_body(informationSource={"reference": ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    bad = medication_statement_body(
        informationSource={"reference": "Practitioner/999999"}
    )
    resp = await client.post(BASE + "/", json=bad)
    assert resp.status_code == 422 and "informationSource" in resp.text


async def test_create_medication_reference_must_exist(client):
    medication = await create_medication(client, medication_body())
    ok = {
        "status": "active",
        "subject": {"reference": "https://other.example.org/fhir/Patient/1"},
        "medicationReference": {"reference": f"Medication/{medication}"},
    }
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = {**ok, "medicationReference": {"reference": "Medication/999999"}}
    resp = await client.post(BASE + "/", json=bad)
    assert resp.status_code == 422 and "medicationReference" in resp.text


async def test_create_part_of_and_reason_reference_must_exist(client):
    patient = await create_patient(client)
    observation = await create_observation(client, observation_body(patient))
    procedure = await create_procedure(client, procedure_body(patient))
    condition = await create_condition(client, condition_body(patient))
    other = await create_medication_statement(
        client, medication_statement_body(patient)
    )
    ok = medication_statement_body(
        partOf=[
            {"reference": f"Observation/{observation}"},
            {"reference": f"Procedure/{procedure}"},
            {"reference": f"MedicationStatement/{other}"},
        ],
        reasonReference=[
            {"reference": f"Condition/{condition}"},
            {"reference": f"Observation/{observation}"},
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for element, ref in (
        ("partOf", "Observation/999999"),
        ("partOf", "Procedure/999999"),
        ("partOf", "MedicationStatement/999999"),
        ("reasonReference", "Condition/999999"),
    ):
        resp = await client.post(
            BASE + "/",
            json=medication_statement_body(**{element: [{"reference": ref}]}),
        )
        assert resp.status_code == 422 and f"{element}[0]" in resp.text, (element, ref)


async def test_create_note_author_and_identifier_assigner_must_exist(client):
    practitioner = await create_practitioner(client)
    ok = medication_statement_body(
        note=[
            {
                "text": "n",
                "authorReference": {"reference": f"Practitioner/{practitioner}"},
            }
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = medication_statement_body(
        note=[{"text": "n", "authorReference": {"reference": "Practitioner/999999"}}]
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422
    bad = medication_statement_body(
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}]
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    body = medication_statement_body(theirs)
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_absolute_logical_and_unmodeled_references_not_resolved(client):
    """An absolute URL, a logical (identifier-only) reference and a type this server does not
    have are stored as sent."""
    body = medication_statement_body(
        subject={"reference": "https://other.example.org/fhir/Patient/1"},
        informationSource={"identifier": {"system": "urn:pr", "value": "P-9"}},
        basedOn=[{"reference": "https://other.example.org/fhir/CarePlan/9"}],
        derivedFrom=[{"reference": "Goal/12"}],
        partOf=[{"reference": "https://other.example.org/fhir/MedicationDispense/9"}],
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["subject"]["reference"] == "https://other.example.org/fhir/Patient/1"
    assert data["informationSource"]["identifier"]["value"] == "P-9"
    assert data["derivedFrom"][0]["reference"] == "Goal/12"
    assert (
        data["partOf"][0]["reference"]
        == "https://other.example.org/fhir/MedicationDispense/9"
    )


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    statement, _ = await _full(client)
    resp = await client.get(f"{BASE}/{statement}")
    assert resp.status_code == 200 and resp.json()["id"] == str(statement)


async def test_get_is_fhir_regardless_of_accept(client):
    statement = await create_medication_statement(client, medication_statement_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{statement}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "MedicationStatement"


async def test_xml_only_accept_is_406(client):
    statement = await create_medication_statement(client, medication_statement_body())
    resp = await client.get(
        f"{BASE}/{statement}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    statement, body = await _full(client)
    resp = await client.patch(f"{BASE}/{statement}", json={"status": "stopped"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "stopped"
    assert resp.json()["dosage"] == body["dosage"]  # untouched
    assert resp.json()["note"] == body["note"]


async def test_patch_reindexes_search(client):
    statement, _ = await _full(client)
    patient = await create_patient(client)
    await client.patch(
        f"{BASE}/{statement}",
        json={
            "status": "stopped",
            "effectivePeriod": {"start": "2030-05-06", "end": "2030-06-06"},
            "subject": {"reference": f"Patient/{patient}"},
            "category": concept_of("inpatient"),
            "partOf": [],
        },
    )
    for param, old, new in (
        ("status", "completed", "stopped"),
        ("effective", "lt2027-01-01", "ge2030-01-01"),
        ("category", "community", "inpatient"),
        ("patient", None, str(patient)),
    ):
        if old is not None:
            assert statement not in _ids(
                (await client.get(BASE + "/", params={param: old})).json()
            ), param
        assert statement in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param
    assert statement in _ids(
        (await client.get(BASE + "/", params={"part-of:missing": "true"})).json()
    )


def concept_of(code: str) -> dict:
    return {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/medication-statement-category",
                "code": code,
            }
        ]
    }


async def test_patch_replaces_the_dosage_list(client):
    statement, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{statement}", json={"dosage": [{"text": "only"}]}
    )
    assert resp.json()["dosage"] == [{"text": "only"}]
    cleared = await client.patch(f"{BASE}/{statement}", json={"dosage": []})
    assert "dosage" not in cleared.json()
    assert cleared.json()["status"] == "completed"  # untouched


async def test_patch_clears_context_and_missing_follows(client):
    encounter = await create_encounter(client, encounter_body())
    statement = await create_medication_statement(
        client,
        medication_statement_body(context={"reference": f"Encounter/{encounter}"}),
    )
    resp = await client.patch(f"{BASE}/{statement}", json={"context": None})
    assert "context" not in resp.json()
    assert statement in _ids(
        (await client.get(BASE + "/", params={"context:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    statement = await create_medication_statement(client, medication_statement_body())
    resp = await client.patch(
        f"{BASE}/{statement}",
        json={"informationSource": {"reference": "Practitioner/999999"}},
    )
    assert resp.status_code == 422
    assert "informationSource" not in (await client.get(f"{BASE}/{statement}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    statement = await create_medication_statement(
        client, medication_statement_body(status="active")
    )
    assert (
        await client.patch(f"{BASE}/{statement}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{statement}")).json()["status"] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "stopped"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    statement, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{statement}")).status_code == 204
    assert (await client.get(f"{BASE}/{statement}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "MS-1001"),
        ("status", "completed"),
        ("category", "community"),
        ("code", "197361"),
    ):
        assert statement not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["medication_statement:read"])
    assert (
        await client.post(BASE + "/", json=medication_statement_body())
    ).status_code == 403


async def test_org_less_token_rejected(client):
    statement = await create_medication_statement(client, medication_statement_body())

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": STATEMENT_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (
        await client.post(BASE + "/", json=medication_statement_body())
    ).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{statement}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    statement = await create_medication_statement(client, medication_statement_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{statement}"),
            await other_client.patch(f"{BASE}/{statement}", json={"status": "stopped"}),
            await other_client.delete(f"{BASE}/{statement}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_medication_statement(
        client,
        medication_statement_body(
            identifier=[{"system": "urn:t", "value": "TenantAOnly"}]
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


# -- Other resources that point at a statement ------------------------------------------------


async def test_a_statement_is_checked_where_a_reference_can_name_it(client):
    """Observation.partOf can name a MedicationStatement: it must exist now that statements are a
    resource here."""
    patient = await create_patient(client)
    statement = await create_medication_statement(
        client, medication_statement_body(patient)
    )
    obs = "/api/fhir/v1/observations"
    ok = observation_body(
        patient, partOf=[{"reference": f"MedicationStatement/{statement}"}]
    )
    assert (await client.post(obs + "/", json=ok)).status_code == 201
    bad = observation_body(
        patient, partOf=[{"reference": "MedicationStatement/999999"}]
    )
    resp = await client.post(obs + "/", json=bad)
    assert resp.status_code == 422 and "partOf" in resp.text

"""Core questionnaire endpoint coverage.

Questionnaire is stored whole in `content` (like QuestionnaireResponse, CareTeam, CarePlan and the
other content-based resources): the request body (genuine FHIR R4 Questionnaire JSON) is validated
and stored in `content`, every response is FHIR R4 (`application/fhir+json`, regardless of
Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/questionnaire.html#search) - the item tree is plain content apart
from `item.code` and `item.definition`.

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence check on `identifier.assigner` and on a relative `Questionnaire/<id>`
in any Reference(Any). Search lives in test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.questionnaire.conftest import QUESTIONNAIRE_PERMS
from tests.integration.questionnaire.support import (
    BASE,
    URL,
    create_organization,
    create_questionnaire,
    full_body,
    questionnaire_body,
    questionnaire_response_body,
)

RESPONSES = "/api/fhir/v1/questionnaire-responses"


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


def _as_user(sub="u-test", org_id="org-test", permissions=QUESTIONNAIRE_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    organization = await create_organization(client)
    body = full_body(organization)
    return await create_questionnaire(client, body), body


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=questionnaire_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    assert resp.json()["resourceType"] == "Questionnaire"
    assert resp.json()["id"] == "380000"  # the first id of the block


async def test_create_full_round_trip_including_the_whole_item_tree(client):
    questionnaire, body = await _full(client)
    data = (await client.get(f"{BASE}/{questionnaire}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_the_nested_tree_in_order(client):
    questionnaire, _ = await _full(client)
    data = (await client.get(f"{BASE}/{questionnaire}")).json()
    assert [i["linkId"] for i in data["item"]] == ["1", "2"]
    assert [i["linkId"] for i in data["item"][0]["item"]] == ["1.1", "1.2"]
    first = data["item"][0]["item"][0]
    assert first["type"] == "open-choice"
    assert [w["operator"] for w in first["enableWhen"]] == ["=", ">="]
    assert first["enableWhen"][1]["answerQuantity"]["comparator"] == ">"
    assert first["answerOption"][0]["initialSelected"] is True


async def test_create_deeply_nested_items(client):
    item = {"linkId": "leaf", "type": "string"}
    for depth in range(12):
        item = {"linkId": f"g{depth}", "type": "group", "item": [item]}
    questionnaire = await create_questionnaire(client, questionnaire_body(item=[item]))
    data = (await client.get(f"{BASE}/{questionnaire}")).json()
    node = data["item"][0]
    for depth in range(11, -1, -1):
        assert node["linkId"] == f"g{depth}"
        node = node["item"][0]
    assert node == {"linkId": "leaf", "type": "string"}


@pytest.mark.parametrize("status", ["draft", "active", "retired", "unknown"])
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=questionnaire_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_every_item_type_round_trips(client):
    types = [
        "group",
        "display",
        "boolean",
        "decimal",
        "integer",
        "date",
        "dateTime",
        "time",
        "string",
        "text",
        "url",
        "choice",
        "open-choice",
        "attachment",
        "reference",
        "quantity",
    ]
    body = questionnaire_body(
        item=[{"linkId": str(i), "type": t} for i, t in enumerate(types)]
    )
    questionnaire = await create_questionnaire(client, body)
    data = (await client.get(f"{BASE}/{questionnaire}")).json()
    assert [i["type"] for i in data["item"]] == types


async def test_create_ignores_server_managed_id_and_meta(client):
    body = questionnaire_body(id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "bogus"},
        {"status": "in_progress"},
        {"identifier": {"value": "x"}},
        {"subjectType": "Patient"},
        {"url": 5},
        {"date": 5},
        {"useContext": {"code": {"code": "x"}}},
        {"jurisdiction": {"coding": []}},
        {"effectivePeriod": "2026"},
        {"item": {"linkId": "1"}},
        {"item": ["x"]},
        {"item": [{"linkId": 1, "type": "group"}]},
        {"item": [{"linkId": "1", "type": "nonsense"}]},
        {"item": [{"linkId": "1", "type": "group", "item": "x"}]},
        {"item": [{"linkId": "1", "type": "choice", "enableBehavior": "some"}]},
    ):
        resp = await client.post(BASE + "/", json=questionnaire_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json=questionnaire_body(not_a_fhir_element=1))
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in (
        {"org_id": "x"},
        {"user_id": "x"},
        {"derived_from": ["x"]},
        {"effective_period_start": "2026-01-01"},
    ):
        resp = await client.post(BASE + "/", json={**questionnaire_body(), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(
        BASE + "/", json=questionnaire_body(resourceType="Patient")
    )
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=questionnaire_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_identifier_assigner_must_exist(client):
    organization = await create_organization(client)
    ok = questionnaire_body(
        identifier=[
            {"value": "1", "assigner": {"reference": f"Organization/{organization}"}}
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = questionnaire_body(
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}]
    )
    resp = await client.post(BASE + "/", json=bad)
    assert resp.status_code == 422 and "assigner" in resp.text


async def test_create_use_context_reference_checked_and_unmodeled_stored(client):
    organization = await create_organization(client)
    context = {"code": {"code": "venue"}}
    ok = questionnaire_body(
        useContext=[
            {**context, "valueReference": {"reference": f"Organization/{organization}"}}
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = questionnaire_body(
        useContext=[{**context, "valueReference": {"reference": "Organization/999999"}}]
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422
    # An absolute URL, and a type this server does not have, are stored as sent.
    stored = questionnaire_body(
        useContext=[
            {
                **context,
                "valueReference": {"reference": "https://other.example.org/Org/1"},
            },
            {**context, "valueReference": {"reference": "ResearchStudy/5"}},
        ]
    )
    assert (await client.post(BASE + "/", json=stored)).status_code == 201


async def test_a_relative_questionnaire_reference_is_checked_in_a_reference_any(client):
    """Questionnaire is now a rebuilt resource: a relative `Questionnaire/<id>` in a
    Reference(Any) (QuestionnaireResponse.subject) must exist; the canonical `questionnaire`
    string of a response is not a Reference, so it is stored as sent."""
    questionnaire = await create_questionnaire(client, questionnaire_body())
    ok = questionnaire_response_body(
        subject={"reference": f"Questionnaire/{questionnaire}"}
    )
    assert (await client.post(RESPONSES + "/", json=ok)).status_code == 201
    bad = questionnaire_response_body(subject={"reference": "Questionnaire/999999"})
    resp = await client.post(RESPONSES + "/", json=bad)
    assert resp.status_code == 422 and "subject" in resp.text
    canonical = questionnaire_response_body(questionnaire="Questionnaire/999999")
    assert (await client.post(RESPONSES + "/", json=canonical)).status_code == 201


async def test_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_organization(other_client)
    finally:
        _as_user()
    body = questionnaire_body(
        identifier=[{"value": "1", "assigner": {"reference": f"Organization/{theirs}"}}]
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    questionnaire, _ = await _full(client)
    resp = await client.get(f"{BASE}/{questionnaire}")
    assert resp.status_code == 200 and resp.json()["id"] == str(questionnaire)


async def test_get_is_fhir_regardless_of_accept(client):
    questionnaire = await create_questionnaire(client, questionnaire_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{questionnaire}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Questionnaire"


async def test_xml_only_accept_is_406(client):
    questionnaire = await create_questionnaire(client, questionnaire_body())
    resp = await client.get(
        f"{BASE}/{questionnaire}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    questionnaire, body = await _full(client)
    resp = await client.patch(f"{BASE}/{questionnaire}", json={"status": "retired"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "retired"
    assert resp.json()["item"] == body["item"]  # untouched
    assert resp.json()["useContext"] == body["useContext"]


async def test_patch_reindexes_search(client):
    questionnaire, _ = await _full(client)
    await client.patch(
        f"{BASE}/{questionnaire}",
        json={
            "status": "retired",
            "title": "Renamed Form",
            "version": "2.0",
            "date": "2030-05-06T07:08:09Z",
            "url": "https://fhir-server.dev/fhir/Questionnaire/renamed",
            "subjectType": ["Encounter"],
            "useContext": [],
        },
    )
    for param, old, new in (
        ("status", "active", "retired"),
        ("title", "Patient Health", "Renamed"),
        ("version", "1.0", "2.0"),
        ("date", "2026", "2030"),
        ("url", URL, "https://fhir-server.dev/fhir/Questionnaire/renamed"),
        ("subject-type", "Patient", "Encounter"),
    ):
        assert questionnaire not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert questionnaire in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param
    assert questionnaire in _ids(
        (await client.get(BASE + "/", params={"context-type:missing": "true"})).json()
    )


async def test_patch_replaces_the_whole_item_tree(client):
    questionnaire, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{questionnaire}",
        json={"item": [{"linkId": "only", "type": "string"}]},
    )
    assert resp.json()["item"] == [{"linkId": "only", "type": "string"}]
    # the item.code / item.definition index follows
    assert questionnaire not in _ids(
        (
            await client.get(BASE + "/", params={"code": "http://loinc.org|44250-9"})
        ).json()
    )
    cleared = await client.patch(f"{BASE}/{questionnaire}", json={"item": []})
    assert "item" not in cleared.json()
    assert cleared.json()["status"] == "active"  # untouched


async def test_patch_clears_an_element_and_missing_follows(client):
    questionnaire = await create_questionnaire(
        client, questionnaire_body(publisher="Example")
    )
    resp = await client.patch(f"{BASE}/{questionnaire}", json={"publisher": None})
    assert "publisher" not in resp.json()
    assert questionnaire in _ids(
        (await client.get(BASE + "/", params={"publisher:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    questionnaire = await create_questionnaire(client, questionnaire_body())
    resp = await client.patch(
        f"{BASE}/{questionnaire}",
        json={
            "identifier": [
                {"value": "1", "assigner": {"reference": "Organization/999999"}}
            ]
        },
    )
    assert resp.status_code == 422
    assert "identifier" not in (await client.get(f"{BASE}/{questionnaire}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    questionnaire = await create_questionnaire(
        client, questionnaire_body(status="active")
    )
    assert (
        await client.patch(f"{BASE}/{questionnaire}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{questionnaire}")).json()["status"] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "retired"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    questionnaire, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{questionnaire}")).status_code == 204
    assert (await client.get(f"{BASE}/{questionnaire}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "PHQ-9"),
        ("status", "active"),
        ("code", "http://loinc.org|44250-9"),
        ("context-type", "focus"),
        ("definition", "http://example.org/definitions/second"),
    ):
        assert questionnaire not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["questionnaire:read"])
    assert (await client.post(BASE + "/", json=questionnaire_body())).status_code == 403


async def test_org_less_token_rejected(client):
    questionnaire = await create_questionnaire(client, questionnaire_body())

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": QUESTIONNAIRE_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=questionnaire_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{questionnaire}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    questionnaire = await create_questionnaire(client, questionnaire_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{questionnaire}"),
            await other_client.patch(
                f"{BASE}/{questionnaire}", json={"status": "retired"}
            ),
            await other_client.delete(f"{BASE}/{questionnaire}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_questionnaire(
        client,
        questionnaire_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()

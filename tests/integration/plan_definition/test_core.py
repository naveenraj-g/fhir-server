"""Core plan-definition endpoint coverage.

PlanDefinition is stored whole in `content` (like Questionnaire, CarePlan and the other
content-based resources): the request body (genuine FHIR R4 PlanDefinition JSON) is validated
and stored in `content`, every response is FHIR R4 (`application/fhir+json`, regardless of
Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/plandefinition.html#search) - everything else (`goal`, the whole
`action` tree apart from `definitionCanonical`, `subtitle`, `purpose`, ...) is plain content.

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`identifier.assigner`,
`subjectReference`, an action's `subjectReference`, `useContext.valueReference`, ...) and on a
relative `PlanDefinition/<id>` in any Reference(Any). Search lives in test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.group.support import create_group, group_body
from tests.integration.plan_definition.conftest import PLAN_DEFINITION_PERMS
from tests.integration.plan_definition.support import (
    BASE,
    create_organization,
    create_plan_definition,
    full_body,
    plan_definition_body,
)

ISSUES = "/api/fhir/v1/detected-issues/"


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


def _as_user(sub="u-test", org_id="org-test", permissions=PLAN_DEFINITION_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    organization = await create_organization(client)
    body = full_body(organization)
    return await create_plan_definition(client, body), body


async def _created(client, **extra) -> int:
    return (
        await client.post(BASE + "/", json=plan_definition_body(**extra))
    ).status_code


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=plan_definition_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    assert resp.json()["resourceType"] == "PlanDefinition"
    assert resp.json()["id"] == "420000"  # the first id of the block


async def test_create_full_round_trip(client):
    plan_definition, body = await _full(client)
    data = (await client.get(f"{BASE}/{plan_definition}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client):
    plan_definition, _ = await _full(client)
    data = (await client.get(f"{BASE}/{plan_definition}")).json()
    assert data["goal"][0]["target"][0]["measure"] == {"text": "steps"}
    assert data["action"][0]["groupingBehavior"] == "logical-group"
    assert (
        data["action"][0]["action"][0]["relatedAction"][0]["relationship"]
        == "after-end"
    )
    assert data["action"][0]["action"][1]["dynamicValue"][0]["path"] == "title"
    assert data["subtitle"] == "After surgery" and data["usage"] == "Use at discharge"
    assert data["relatedArtifact"][0]["type"] == "documentation"


@pytest.mark.parametrize("status", ["draft", "active", "retired", "unknown"])
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=plan_definition_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_deeply_nested_actions_round_trip_in_order(client):
    tree = [
        {
            "title": "1",
            "action": [
                {"title": "1.1", "action": [{"title": "1.1.1"}]},
                {"title": "1.2"},
            ],
        },
        {"title": "2"},
    ]
    resp = await client.post(BASE + "/", json=plan_definition_body(action=tree))
    assert resp.status_code == 201, resp.text
    assert resp.json()["action"] == tree


async def test_create_ignores_server_managed_id_and_meta(client):
    body = plan_definition_body(id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "robot"},
        {"type": "order-set"},
        {"identifier": {"value": "x"}},
        {"topic": {"text": "x"}},
        {"jurisdiction": "US"},
        {"useContext": "x"},
        {"relatedArtifact": {"type": "x"}},
        {"library": "http://x"},
        {"effectivePeriod": "2026"},
        {"date": 5},
        {"doNotPerform": "maybe"},
        {"goal": {"id": "g"}},
        {"action": {"title": "x"}},
        {"action": [{"title": 5}]},
        {"subtitle": 5},
    ):
        resp = await client.post(BASE + "/", json=plan_definition_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(
        BASE + "/", json=plan_definition_body(not_a_fhir_element=1)
    )
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in (
        {"type_text": "x"},
        {"timing_date_time": "2026-01-01"},
        {"org_id": "x"},
    ):
        resp = await client.post(BASE + "/", json=plan_definition_body(**stale))
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(
        BASE + "/", json=plan_definition_body(resourceType="Patient")
    )
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=plan_definition_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_identifier_assigner_must_exist(client):
    organization = await create_organization(client)
    ok = plan_definition_body(
        identifier=[
            {"value": "1", "assigner": {"reference": f"Organization/{organization}"}}
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = plan_definition_body(
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}]
    )
    resp = await client.post(BASE + "/", json=bad)
    assert resp.status_code == 422 and "assigner" in resp.text


async def test_create_subject_and_action_references_must_exist(client):
    group = await create_group(client, group_body())
    assert (
        await _created(client, subjectReference={"reference": f"Group/{group}"}) == 201
    )
    assert await _created(client, subjectReference={"reference": "Group/999999"}) == 422
    ok = [{"title": "x", "subjectReference": {"reference": f"Group/{group}"}}]
    assert await _created(client, action=ok) == 201
    bad = [
        {
            "title": "outer",
            "action": [{"subjectReference": {"reference": "Group/999999"}}],
        }
    ]
    resp = await client.post(BASE + "/", json=plan_definition_body(action=bad))
    assert resp.status_code == 422 and "action[0].action[0]" in resp.text


async def test_create_use_context_reference_checked_and_unmodeled_stored(client):
    organization = await create_organization(client)
    context = {"code": {"code": "venue"}}
    ok = plan_definition_body(
        useContext=[
            {**context, "valueReference": {"reference": f"Organization/{organization}"}}
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = plan_definition_body(
        useContext=[{**context, "valueReference": {"reference": "Organization/999999"}}]
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422
    # An absolute URL, and a type this server does not have, are stored as sent.
    stored = plan_definition_body(
        useContext=[
            {
                **context,
                "valueReference": {"reference": "https://other.example.org/Org/1"},
            },
            {**context, "valueReference": {"reference": "ResearchStudy/5"}},
        ]
    )
    assert (await client.post(BASE + "/", json=stored)).status_code == 201


async def test_canonical_urls_are_never_existence_checked(client):
    """relatedArtifact.resource, library and an action's definitionCanonical are canonical strings, not Reference
    objects: even a relative `PlanDefinition/<id>` that does not exist is stored as sent."""
    body = plan_definition_body(
        relatedArtifact=[
            {"type": "predecessor", "resource": "PlanDefinition/999999"},
            {"type": "depends-on", "resource": "http://example.org/fhir/Library/x"},
        ],
        library=["Library/999999"],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_a_relative_plan_definition_reference_is_checked_in_a_reference_any(
    client,
):
    """PlanDefinition is a rebuilt resource: a relative `PlanDefinition/<id>` in a
    Reference(Any) (DetectedIssue.implicated) must exist."""
    plan_definition = await create_plan_definition(client, plan_definition_body())
    ok = {
        "status": "final",
        "implicated": [{"reference": f"PlanDefinition/{plan_definition}"}],
    }
    assert (await client.post(ISSUES, json=ok)).status_code == 201
    bad = {
        "status": "final",
        "implicated": [{"reference": "PlanDefinition/999999"}],
    }
    resp = await client.post(ISSUES, json=bad)
    assert resp.status_code == 422 and "implicated" in resp.text


async def test_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_organization(other_client)
    finally:
        _as_user()
    body = plan_definition_body(
        identifier=[{"value": "1", "assigner": {"reference": f"Organization/{theirs}"}}]
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    plan_definition, _ = await _full(client)
    resp = await client.get(f"{BASE}/{plan_definition}")
    assert resp.status_code == 200 and resp.json()["id"] == str(plan_definition)


async def test_get_is_fhir_regardless_of_accept(client):
    plan_definition = await create_plan_definition(client, plan_definition_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{plan_definition}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "PlanDefinition"


async def test_xml_only_accept_is_406(client):
    plan_definition = await create_plan_definition(client, plan_definition_body())
    resp = await client.get(
        f"{BASE}/{plan_definition}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    plan_definition, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{plan_definition}", json={"status": "retired", "version": "2.0"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "retired" and resp.json()["version"] == "2.0"
    assert resp.json()["name"] == "DischargePathway"  # untouched
    assert resp.json()["goal"][0]["id"] == "g1"  # untouched


async def test_patch_reindexes_search(client):
    plan_definition, _ = await _full(client)
    patched = await client.patch(
        f"{BASE}/{plan_definition}",
        json={
            "status": "retired",
            "name": "Renamed",
            "date": "2027-03-03",
            "effectivePeriod": {"start": "2027-01-01"},
            "topic": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/definition-topic",
                            "code": "education",
                        }
                    ]
                }
            ],
            "relatedArtifact": [
                {
                    "type": "successor",
                    "resource": "http://example.org/fhir/PlanDefinition/next",
                }
            ],
        },
    )
    assert patched.status_code == 200, patched.text
    for param, old, new in (
        ("status", "active", "retired"),
        ("name", "dischargepathway", "renamed"),
        ("date", "2026-01-15", "2027-03-03"),
        ("effective", None, "ge2027-06-01"),
        ("topic", "treatment", "education"),
        ("composed-of", "http://example.org/fhir/Library/x", None),
        ("successor", None, "http://example.org/fhir/PlanDefinition/next"),
    ):
        if old:
            assert plan_definition not in _ids(
                (await client.get(BASE + "/", params={param: old})).json()
            ), param
        if new:
            assert plan_definition in _ids(
                (await client.get(BASE + "/", params={param: new})).json()
            ), param


async def test_patch_replaces_lists_and_empty_clears(client):
    plan_definition, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{plan_definition}",
        json={
            "identifier": [],
            "topic": [],
            "relatedArtifact": [],
            "useContext": [],
            "action": [],
        },
    )
    for gone in ("identifier", "topic", "relatedArtifact", "useContext", "action"):
        assert gone not in resp.json()
    assert resp.json()["status"] == "active"  # untouched
    for param in ("identifier", "topic", "composed-of", "context-type", "definition"):
        assert plan_definition in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_an_element_and_missing_follows(client):
    plan_definition, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{plan_definition}",
        json={"url": None, "effectivePeriod": None, "date": None, "type": None},
    )
    assert all(k not in resp.json() for k in ("url", "effectivePeriod", "date", "type"))
    for param in ("url", "effective", "date", "type"):
        assert plan_definition in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    plan_definition = await create_plan_definition(client, plan_definition_body())
    resp = await client.patch(
        f"{BASE}/{plan_definition}",
        json={"action": [{"subjectReference": {"reference": "Group/999999"}}]},
    )
    assert resp.status_code == 422
    assert "action" not in (await client.get(f"{BASE}/{plan_definition}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    plan_definition = await create_plan_definition(client, plan_definition_body())
    assert (
        await client.patch(f"{BASE}/{plan_definition}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{plan_definition}")).json()["status"] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "active"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    plan_definition, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{plan_definition}")).status_code == 204
    assert (await client.get(f"{BASE}/{plan_definition}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "AD-1001"),
        ("topic", "treatment"),
        ("composed-of", "http://example.org/fhir/Library/x"),
        ("definition", "http://example.org/fhir/ActivityDefinition/visit"),
        ("type", "clinical-protocol"),
    ):
        assert plan_definition not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["plan_definition:read"])
    assert (
        await client.post(BASE + "/", json=plan_definition_body())
    ).status_code == 403


async def test_org_less_token_rejected(client):
    plan_definition = await create_plan_definition(client, plan_definition_body())

    async def _no_org(request: Request):
        request.state.user = {
            "sub": "u-test",
            "permissions": PLAN_DEFINITION_PERMS,
        }

    app.dependency_overrides[get_current_user] = _no_org
    assert (
        await client.post(BASE + "/", json=plan_definition_body())
    ).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{plan_definition}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    plan_definition = await create_plan_definition(client, plan_definition_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{plan_definition}"),
            await other_client.patch(
                f"{BASE}/{plan_definition}", json={"status": "active"}
            ),
            await other_client.delete(f"{BASE}/{plan_definition}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_plan_definition(
        client,
        plan_definition_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()

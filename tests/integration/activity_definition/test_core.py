"""Core activity-definition endpoint coverage.

ActivityDefinition is stored whole in `content` (like Questionnaire, CarePlan and the other
content-based resources): the request body (genuine FHIR R4 ActivityDefinition JSON) is validated
and stored in `content`, every response is FHIR R4 (`application/fhir+json`, regardless of
Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/activitydefinition.html#search) - everything else (`kind`, `code`,
`timing[x]`, `participant`, `product[x]`, `dosage`, `dynamicValue`, ...) is plain content.

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`identifier.assigner`,
`subjectReference`, `location`, `productReference`, `useContext.valueReference`, ...) and on a
relative `ActivityDefinition/<id>` in any Reference(Any). Search lives in test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.activity_definition.conftest import ACTIVITY_DEFINITION_PERMS
from tests.integration.activity_definition.support import (
    BASE,
    activity_definition_body,
    create_activity_definition,
    create_organization,
    full_body,
)
from tests.integration.group.support import create_group, group_body
from tests.integration.location.support import create_location

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


def _as_user(sub="u-test", org_id="org-test", permissions=ACTIVITY_DEFINITION_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    organization = await create_organization(client)
    body = full_body(organization)
    return await create_activity_definition(client, body), body


async def _created(client, **extra) -> int:
    return (
        await client.post(BASE + "/", json=activity_definition_body(**extra))
    ).status_code


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=activity_definition_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    assert resp.json()["resourceType"] == "ActivityDefinition"
    assert resp.json()["id"] == "410000"  # the first id of the block


async def test_create_full_round_trip(client):
    activity_definition, body = await _full(client)
    data = (await client.get(f"{BASE}/{activity_definition}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client):
    activity_definition, _ = await _full(client)
    data = (await client.get(f"{BASE}/{activity_definition}")).json()
    assert data["kind"] == "ServiceRequest" and data["intent"] == "order"
    assert data["timingTiming"]["repeat"]["frequency"] == 1
    assert data["dosage"][0]["route"] == {"text": "oral"}
    assert data["dynamicValue"][0]["path"] == "priority"
    assert data["participant"][0]["role"] == {"text": "nurse"}
    assert data["relatedArtifact"][0]["type"] == "documentation"


@pytest.mark.parametrize("status", ["draft", "active", "retired", "unknown"])
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=activity_definition_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_every_timing_choice_round_trips(client):
    for key, value in (
        ("timingTiming", {"repeat": {"frequency": 2}}),
        ("timingDateTime", "2026-02-01T09:00:00Z"),
        ("timingAge", {"value": 3, "unit": "years"}),
        ("timingPeriod", {"start": "2026-01-01", "end": "2026-02-01"}),
        ("timingRange", {"low": {"value": 1}, "high": {"value": 2}}),
        ("timingDuration", {"value": 4, "unit": "h"}),
    ):
        resp = await client.post(
            BASE + "/", json=activity_definition_body(**{key: value})
        )
        assert resp.status_code == 201, (key, resp.text)
        assert resp.json()[key] == value


async def test_create_ignores_server_managed_id_and_meta(client):
    body = activity_definition_body(
        id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "robot"},
        {"kind": "Banana"},
        {"intent": "maybe"},
        {"priority": "now"},
        {"identifier": {"value": "x"}},
        {"topic": {"text": "x"}},
        {"jurisdiction": "US"},
        {"useContext": "x"},
        {"relatedArtifact": {"type": "x"}},
        {"library": "http://x"},
        {"effectivePeriod": "2026"},
        {"date": 5},
        {"doNotPerform": "maybe"},
        {"participant": "x"},
        {"dosage": {"text": "x"}},
        {"location": "Location/1"},
        {"specimenRequirement": {"reference": "SpecimenDefinition/1"}},
    ):
        resp = await client.post(BASE + "/", json=activity_definition_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(
        BASE + "/", json=activity_definition_body(not_a_fhir_element=1)
    )
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in (
        {"code_text": "x"},
        {"timing_date_time": "2026-01-01"},
        {"org_id": "x"},
    ):
        resp = await client.post(BASE + "/", json=activity_definition_body(**stale))
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(
        BASE + "/", json=activity_definition_body(resourceType="Patient")
    )
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=activity_definition_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_identifier_assigner_must_exist(client):
    organization = await create_organization(client)
    ok = activity_definition_body(
        identifier=[
            {"value": "1", "assigner": {"reference": f"Organization/{organization}"}}
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = activity_definition_body(
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}]
    )
    resp = await client.post(BASE + "/", json=bad)
    assert resp.status_code == 422 and "assigner" in resp.text


async def test_create_subject_location_and_product_must_exist(client):
    group = await create_group(client, group_body())
    location = await create_location(client)
    assert (
        await _created(client, subjectReference={"reference": f"Group/{group}"}) == 201
    )
    assert await _created(client, subjectReference={"reference": "Group/999999"}) == 422
    assert await _created(client, location={"reference": f"Location/{location}"}) == 201
    assert await _created(client, location={"reference": "Location/999999"}) == 422
    assert (
        await _created(client, productReference={"reference": "Medication/999999"})
        == 422
    )


async def test_create_use_context_reference_checked_and_unmodeled_stored(client):
    organization = await create_organization(client)
    context = {"code": {"code": "venue"}}
    ok = activity_definition_body(
        useContext=[
            {**context, "valueReference": {"reference": f"Organization/{organization}"}}
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = activity_definition_body(
        useContext=[{**context, "valueReference": {"reference": "Organization/999999"}}]
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422
    # An absolute URL, and a type this server does not have, are stored as sent.
    stored = activity_definition_body(
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
    """relatedArtifact.resource, library and transform are canonical strings, not Reference
    objects: even a relative `ActivityDefinition/<id>` that does not exist is stored as sent."""
    body = activity_definition_body(
        relatedArtifact=[
            {"type": "predecessor", "resource": "ActivityDefinition/999999"},
            {"type": "depends-on", "resource": "http://example.org/fhir/Library/x"},
        ],
        library=["Library/999999"],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_a_relative_activity_definition_reference_is_checked_in_a_reference_any(
    client,
):
    """ActivityDefinition is a rebuilt resource: a relative `ActivityDefinition/<id>` in a
    Reference(Any) (DetectedIssue.implicated) must exist."""
    activity_definition = await create_activity_definition(
        client, activity_definition_body()
    )
    ok = {
        "status": "final",
        "implicated": [{"reference": f"ActivityDefinition/{activity_definition}"}],
    }
    assert (await client.post(ISSUES, json=ok)).status_code == 201
    bad = {
        "status": "final",
        "implicated": [{"reference": "ActivityDefinition/999999"}],
    }
    resp = await client.post(ISSUES, json=bad)
    assert resp.status_code == 422 and "implicated" in resp.text


async def test_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_organization(other_client)
    finally:
        _as_user()
    body = activity_definition_body(
        identifier=[{"value": "1", "assigner": {"reference": f"Organization/{theirs}"}}]
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    activity_definition, _ = await _full(client)
    resp = await client.get(f"{BASE}/{activity_definition}")
    assert resp.status_code == 200 and resp.json()["id"] == str(activity_definition)


async def test_get_is_fhir_regardless_of_accept(client):
    activity_definition = await create_activity_definition(
        client, activity_definition_body()
    )
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{activity_definition}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "ActivityDefinition"


async def test_xml_only_accept_is_406(client):
    activity_definition = await create_activity_definition(
        client, activity_definition_body()
    )
    resp = await client.get(
        f"{BASE}/{activity_definition}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    activity_definition, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{activity_definition}", json={"status": "retired", "version": "2.0"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "retired" and resp.json()["version"] == "2.0"
    assert resp.json()["name"] == "FollowUp"  # untouched
    assert resp.json()["dosage"][0]["text"] == "2 mL once"  # untouched


async def test_patch_reindexes_search(client):
    activity_definition, _ = await _full(client)
    patched = await client.patch(
        f"{BASE}/{activity_definition}",
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
                    "resource": "http://example.org/fhir/ActivityDefinition/next",
                }
            ],
        },
    )
    assert patched.status_code == 200, patched.text
    for param, old, new in (
        ("status", "active", "retired"),
        ("name", "followup", "renamed"),
        ("date", "2026-01-15", "2027-03-03"),
        ("effective", None, "ge2027-06-01"),
        ("topic", "treatment", "education"),
        ("composed-of", "http://example.org/fhir/Library/x", None),
        ("successor", None, "http://example.org/fhir/ActivityDefinition/next"),
    ):
        if old:
            assert activity_definition not in _ids(
                (await client.get(BASE + "/", params={param: old})).json()
            ), param
        if new:
            assert activity_definition in _ids(
                (await client.get(BASE + "/", params={param: new})).json()
            ), param


async def test_patch_replaces_lists_and_empty_clears(client):
    activity_definition, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{activity_definition}",
        json={"identifier": [], "topic": [], "relatedArtifact": [], "useContext": []},
    )
    for gone in ("identifier", "topic", "relatedArtifact", "useContext"):
        assert gone not in resp.json()
    assert resp.json()["status"] == "active"  # untouched
    for param in ("identifier", "topic", "composed-of", "context-type"):
        assert activity_definition in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_an_element_and_missing_follows(client):
    activity_definition, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{activity_definition}",
        json={"url": None, "effectivePeriod": None, "date": None},
    )
    assert all(k not in resp.json() for k in ("url", "effectivePeriod", "date"))
    for param in ("url", "effective", "date"):
        assert activity_definition in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    activity_definition = await create_activity_definition(
        client, activity_definition_body()
    )
    resp = await client.patch(
        f"{BASE}/{activity_definition}",
        json={"location": {"reference": "Location/999999"}},
    )
    assert resp.status_code == 422
    assert "location" not in (await client.get(f"{BASE}/{activity_definition}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    activity_definition = await create_activity_definition(
        client, activity_definition_body()
    )
    assert (
        await client.patch(f"{BASE}/{activity_definition}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{activity_definition}")).json()[
        "status"
    ] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "active"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    activity_definition, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{activity_definition}")).status_code == 204
    assert (await client.get(f"{BASE}/{activity_definition}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "AD-1001"),
        ("topic", "treatment"),
        ("composed-of", "http://example.org/fhir/Library/x"),
    ):
        assert activity_definition not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["activity_definition:read"])
    assert (
        await client.post(BASE + "/", json=activity_definition_body())
    ).status_code == 403


async def test_org_less_token_rejected(client):
    activity_definition = await create_activity_definition(
        client, activity_definition_body()
    )

    async def _no_org(request: Request):
        request.state.user = {
            "sub": "u-test",
            "permissions": ACTIVITY_DEFINITION_PERMS,
        }

    app.dependency_overrides[get_current_user] = _no_org
    assert (
        await client.post(BASE + "/", json=activity_definition_body())
    ).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{activity_definition}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    activity_definition = await create_activity_definition(
        client, activity_definition_body()
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{activity_definition}"),
            await other_client.patch(
                f"{BASE}/{activity_definition}", json={"status": "active"}
            ),
            await other_client.delete(f"{BASE}/{activity_definition}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_activity_definition(
        client,
        activity_definition_body(
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

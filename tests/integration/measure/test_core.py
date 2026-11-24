"""Core measure endpoint coverage.

Measure is stored whole in `content` (like Questionnaire, CarePlan and the other
content-based resources): the request body (genuine FHIR R4 Measure JSON) is validated
and stored in `content`, every response is FHIR R4 (`application/fhir+json`, regardless of
Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/measure.html#search) - everything else (`scoring`, `type`,
`group` and its population / stratifier tree, `supplementalData`, ...) is plain content.

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`identifier.assigner`,
`subjectReference`, `useContext.valueReference`, ...) and on a
relative `Measure/<id>` in any Reference(Any). Search lives in test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.measure.conftest import MEASURE_PERMS
from tests.integration.measure.support import (
    BASE,
    measure_body,
    create_measure,
    create_organization,
    full_body,
)
from tests.integration.group.support import create_group, group_body

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


def _as_user(sub="u-test", org_id="org-test", permissions=MEASURE_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    organization = await create_organization(client)
    body = full_body(organization)
    return await create_measure(client, body), body


async def _created(client, **extra) -> int:
    return (await client.post(BASE + "/", json=measure_body(**extra))).status_code


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=measure_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    assert resp.json()["resourceType"] == "Measure"
    assert resp.json()["id"] == "560000"  # the first id of the block


async def test_create_full_round_trip(client):
    measure, body = await _full(client)
    data = (await client.get(f"{BASE}/{measure}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client):
    measure, _ = await _full(client)
    data = (await client.get(f"{BASE}/{measure}")).json()
    assert data["scoring"]["coding"][0]["code"] == "proportion"
    group = data["group"][0]
    assert [p["criteria"]["expression"] for p in group["population"]] == [
        "Initial Population",
        "Numerator",
    ]
    assert group["stratifier"][1]["component"][1]["code"] == {"text": "ward"}
    assert data["supplementalData"][0]["usage"] == [{"text": "supplemental-data"}]
    assert data["improvementNotation"] == {"text": "increase"}
    assert data["relatedArtifact"][0]["type"] == "documentation"


@pytest.mark.parametrize("status", ["draft", "active", "retired", "unknown"])
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=measure_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_deeply_nested_group_round_trips_in_order(client):
    criteria = {"language": "text/cql", "expression": "x"}
    groups = [
        {
            "description": "g1",
            "population": [
                {"description": "p1", "criteria": criteria},
                {"description": "p2", "criteria": criteria},
            ],
            "stratifier": [
                {
                    "description": "s1",
                    "component": [
                        {"description": "c1", "criteria": criteria},
                        {"description": "c2", "criteria": criteria},
                    ],
                }
            ],
        },
        {"description": "g2"},
    ]
    resp = await client.post(BASE + "/", json=measure_body(group=groups))
    assert resp.status_code == 201, resp.text
    assert resp.json()["group"] == groups


async def test_create_ignores_server_managed_id_and_meta(client):
    body = measure_body(id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "robot"},
        {"identifier": {"value": "x"}},
        {"topic": {"text": "x"}},
        {"jurisdiction": "US"},
        {"useContext": "x"},
        {"relatedArtifact": {"type": "x"}},
        {"library": "http://x"},
        {"scoring": "proportion"},
        {"type": {"text": "process"}},
        {"definition": "x"},
        {"improvementNotation": "increase"},
        {"effectivePeriod": "2026"},
        {"date": 5},
        {"group": {"description": "x"}},
        {"group": [{"population": {"description": "x"}}]},
        {"supplementalData": {"code": {}}},
        {"disclaimer": 5},
    ):
        resp = await client.post(BASE + "/", json=measure_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json=measure_body(not_a_fhir_element=1))
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in (
        {"scoring_text": "x"},
        {"timing_date_time": "2026-01-01"},
        {"org_id": "x"},
    ):
        resp = await client.post(BASE + "/", json=measure_body(**stale))
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(BASE + "/", json=measure_body(resourceType="Patient"))
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=measure_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_identifier_assigner_must_exist(client):
    organization = await create_organization(client)
    ok = measure_body(
        identifier=[
            {"value": "1", "assigner": {"reference": f"Organization/{organization}"}}
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = measure_body(
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}]
    )
    resp = await client.post(BASE + "/", json=bad)
    assert resp.status_code == 422 and "assigner" in resp.text


async def test_create_subject_and_nested_references_must_exist(client):
    group = await create_group(client, group_body())
    assert (
        await _created(client, subjectReference={"reference": f"Group/{group}"}) == 201
    )
    assert await _created(client, subjectReference={"reference": "Group/999999"}) == 422


async def test_create_use_context_reference_checked_and_unmodeled_stored(client):
    organization = await create_organization(client)
    context = {"code": {"code": "venue"}}
    ok = measure_body(
        useContext=[
            {**context, "valueReference": {"reference": f"Organization/{organization}"}}
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = measure_body(
        useContext=[{**context, "valueReference": {"reference": "Organization/999999"}}]
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422
    # An absolute URL, and a type this server does not have, are stored as sent.
    stored = measure_body(
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
    """relatedArtifact.resource and library are canonical strings, not Reference
    objects: even a relative `Measure/<id>` that does not exist is stored as sent."""
    body = measure_body(
        relatedArtifact=[
            {"type": "predecessor", "resource": "Measure/999999"},
            {"type": "depends-on", "resource": "http://example.org/fhir/Library/x"},
        ],
        library=["Library/999999"],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_a_relative_measure_reference_is_checked_in_a_reference_any(
    client,
):
    """Measure is a rebuilt resource: a relative `Measure/<id>` in a
    Reference(Any) (DetectedIssue.implicated) must exist."""
    measure = await create_measure(client, measure_body())
    ok = {
        "status": "final",
        "implicated": [{"reference": f"Measure/{measure}"}],
    }
    assert (await client.post(ISSUES, json=ok)).status_code == 201
    bad = {
        "status": "final",
        "implicated": [{"reference": "Measure/999999"}],
    }
    resp = await client.post(ISSUES, json=bad)
    assert resp.status_code == 422 and "implicated" in resp.text


async def test_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_organization(other_client)
    finally:
        _as_user()
    body = measure_body(
        identifier=[{"value": "1", "assigner": {"reference": f"Organization/{theirs}"}}]
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    measure, _ = await _full(client)
    resp = await client.get(f"{BASE}/{measure}")
    assert resp.status_code == 200 and resp.json()["id"] == str(measure)


async def test_get_is_fhir_regardless_of_accept(client):
    measure = await create_measure(client, measure_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{measure}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Measure"


async def test_xml_only_accept_is_406(client):
    measure = await create_measure(client, measure_body())
    resp = await client.get(
        f"{BASE}/{measure}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    measure, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{measure}", json={"status": "retired", "version": "2.0"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "retired" and resp.json()["version"] == "2.0"
    assert resp.json()["name"] == "FollowUp"  # untouched
    assert resp.json()["group"][0]["description"] == "Overall"  # untouched


async def test_patch_reindexes_search(client):
    measure, _ = await _full(client)
    patched = await client.patch(
        f"{BASE}/{measure}",
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
                    "resource": "http://example.org/fhir/Measure/next",
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
        ("successor", None, "http://example.org/fhir/Measure/next"),
    ):
        if old:
            assert measure not in _ids(
                (await client.get(BASE + "/", params={param: old})).json()
            ), param
        if new:
            assert measure in _ids(
                (await client.get(BASE + "/", params={param: new})).json()
            ), param


async def test_patch_replaces_lists_and_empty_clears(client):
    measure, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{measure}",
        json={"identifier": [], "topic": [], "relatedArtifact": [], "useContext": []},
    )
    for gone in ("identifier", "topic", "relatedArtifact", "useContext"):
        assert gone not in resp.json()
    assert resp.json()["status"] == "active"  # untouched
    for param in ("identifier", "topic", "composed-of", "context-type"):
        assert measure in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_an_element_and_missing_follows(client):
    measure, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{measure}",
        json={"url": None, "effectivePeriod": None, "date": None},
    )
    assert all(k not in resp.json() for k in ("url", "effectivePeriod", "date"))
    for param in ("url", "effective", "date"):
        assert measure in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    measure = await create_measure(client, measure_body())
    resp = await client.patch(
        f"{BASE}/{measure}",
        json={"subjectReference": {"reference": "Group/999999"}},
    )
    assert resp.status_code == 422
    assert "subjectReference" not in (await client.get(f"{BASE}/{measure}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    measure = await create_measure(client, measure_body())
    assert (
        await client.patch(f"{BASE}/{measure}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{measure}")).json()["status"] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "active"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    measure, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{measure}")).status_code == 204
    assert (await client.get(f"{BASE}/{measure}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "AD-1001"),
        ("topic", "treatment"),
        ("composed-of", "http://example.org/fhir/Library/x"),
    ):
        assert measure not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["measure:read"])
    assert (await client.post(BASE + "/", json=measure_body())).status_code == 403


async def test_org_less_token_rejected(client):
    measure = await create_measure(client, measure_body())

    async def _no_org(request: Request):
        request.state.user = {
            "sub": "u-test",
            "permissions": MEASURE_PERMS,
        }

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=measure_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{measure}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    measure = await create_measure(client, measure_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{measure}"),
            await other_client.patch(f"{BASE}/{measure}", json={"status": "active"}),
            await other_client.delete(f"{BASE}/{measure}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_measure(
        client,
        measure_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()

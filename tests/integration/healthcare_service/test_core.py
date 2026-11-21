"""Core healthcare-service endpoint coverage.

HealthcareService is stored Medplum-style (like Organization/Location/
Practitioner): the request body (genuine FHIR R4 HealthcareService JSON) is
validated and stored whole in `content`, every response is FHIR R4
(`application/fhir+json`, regardless of Accept), and only the FHIR R4 search
parameters are indexed
(https://www.hl7.org/fhir/R4/healthcareservice.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing
scope, cross-org isolation). Search lives in test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.healthcare_service.support import (
    BASE,
    FULL,
    MINIMAL,
    create_healthcare_service,
    create_organization,
    seed_location,
)

PERMS = [
    "healthcare_service:create",
    "healthcare_service:read",
    "healthcare_service:update",
    "healthcare_service:delete",
    "organization:create",
    "organization:read",
    "location:read",
]


@pytest.fixture
def native_validation(monkeypatch):
    """configs/config.yaml ships with fhir_validation.enabled=false, which
    skips base R4 validation entirely. Tests that assert "a key that isn't
    FHIR is a 422" need the validator on: the project's own structural check
    (no sidecar needed)."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "HealthcareService"
    assert data["name"] == "Test Healthcare Service" and data["active"] is True


async def test_create_full_round_trip(client, _engine):
    org = await create_organization(client)
    loc = await seed_location(_engine)
    body = {
        **FULL,
        "providedBy": {"reference": f"Organization/{org}"},
        "location": [{"reference": f"Location/{loc}"}],
        "coverageArea": [{"reference": f"Location/{loc}"}],
    }
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected
    assert (await client.get(f"{BASE}/{data['id']}")).json() == data


async def test_create_keeps_elements_nothing_searches_on(client):
    """eligibility, availableTime, notAvailable, referralMethod, communication,
    telecom, ... have no search parameter — they live only in `content`."""
    data = (await client.post(BASE + "/", json=FULL)).json()
    assert data["availableTime"][0]["daysOfWeek"] == ["mon", "tue"]
    assert data["notAvailable"][0]["description"] == "Closed for the holidays"
    assert data["eligibility"][0]["comment"] == "Adults only"
    assert data["referralMethod"][0]["coding"][0]["code"] == "phone"
    assert data["telecom"][0]["value"] == "555-0100"


async def test_create_ignores_server_managed_id_and_meta(client):
    resp = await client.post(
        BASE + "/",
        json={**MINIMAL, "id": "999", "meta": {"lastUpdated": "2000-01-01T00:00:00Z"}},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json={**MINIMAL, "not_a_fhir_element": 1})
    assert resp.status_code == 422, resp.text


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in (
        {"extra_details": "x"},
        {"appointment_required": True},
        {"org_id": "x"},
        {"user_id": "u"},
    ):
        resp = await client.post(BASE + "/", json={**MINIMAL, **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "resourceType": "Patient"})
    assert resp.status_code == 422, resp.text


async def test_create_bad_day_of_week_rejected(client):
    body = {**MINIMAL, "availableTime": [{"daysOfWeek": ["funday"]}]}
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_not_available_needs_description(client):
    body = {**MINIMAL, "notAvailable": [{"during": {"start": "2026-12-24T00:00:00Z"}}]}
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=MINIMAL)).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


async def test_create_provided_by_must_exist(client):
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "providedBy": {"reference": "Organization/999999"}}
    )
    assert resp.status_code == 422, resp.text


async def test_create_location_and_coverage_area_must_exist(client):
    for element in ("location", "coverageArea"):
        resp = await client.post(
            BASE + "/", json={**MINIMAL, element: [{"reference": "Location/999999"}]}
        )
        assert resp.status_code == 422, (element, resp.text)


async def test_create_identifier_assigner_must_exist(client):
    body = {
        **MINIMAL,
        "identifier": [
            {"value": "1", "assigner": {"reference": "Organization/999999"}}
        ],
    }
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_absolute_references_stored_not_resolved(client):
    ref = "https://other.example.org/fhir/Location/42"
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "location": [{"reference": ref}]}
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["location"][0]["reference"] == ref


async def test_create_logical_reference_without_resource(client):
    body = {
        **MINIMAL,
        "providedBy": {"identifier": {"system": "urn:registry", "value": "ORG-9"}},
    }
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        other_org = await create_organization(other_client, "Other Tenant Org")
    finally:
        _as_user()
    resp = await client.post(
        BASE + "/",
        json={**MINIMAL, "providedBy": {"reference": f"Organization/{other_org}"}},
    )
    assert resp.status_code == 422, resp.text


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client):
    hs = await create_healthcare_service(client, FULL)
    resp = await client.get(f"{BASE}/{hs}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(hs)


async def test_get_is_fhir_regardless_of_accept(client):
    hs = await create_healthcare_service(client)
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{hs}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "HealthcareService"


async def test_xml_only_accept_is_406(client):
    hs = await create_healthcare_service(client)
    resp = await client.get(f"{BASE}/{hs}", headers={"Accept": "application/fhir+xml"})
    assert resp.status_code == 406
    assert resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client):
    hs = await create_healthcare_service(client, FULL)
    resp = await client.patch(f"{BASE}/{hs}", json={"active": False, "name": "Renamed"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["active"] is False and resp.json()["name"] == "Renamed"
    assert resp.json()["availableTime"][0]["daysOfWeek"] == ["mon", "tue"]


async def test_patch_reindexes_search(client):
    hs = await create_healthcare_service(client, FULL)
    await client.patch(f"{BASE}/{hs}", json={"name": "Renamed Service"})
    old = await client.get(BASE + "/", params={"name": "Cardiology"})
    new = await client.get(BASE + "/", params={"name": "Renamed"})
    assert hs not in _ids(old.json())
    assert hs in _ids(new.json())


async def test_patch_replaces_list_wholesale_and_empty_clears(client):
    hs = await create_healthcare_service(client, FULL)
    resp = await client.patch(
        f"{BASE}/{hs}", json={"specialty": [{"coding": [{"code": "NEW"}]}]}
    )
    assert resp.json()["specialty"] == [{"coding": [{"code": "NEW"}]}]
    assert hs not in _ids(
        (await client.get(BASE + "/", params={"specialty": "394579002"})).json()
    )
    assert hs in _ids(
        (await client.get(BASE + "/", params={"specialty": "NEW"})).json()
    )
    resp = await client.patch(f"{BASE}/{hs}", json={"specialty": []})
    assert "specialty" not in resp.json()
    assert hs not in _ids(
        (await client.get(BASE + "/", params={"specialty": "NEW"})).json()
    )


async def test_patch_provided_by_resolved_then_cleared(client):
    org = await create_organization(client)
    hs = await create_healthcare_service(client)
    await client.patch(
        f"{BASE}/{hs}", json={"providedBy": {"reference": f"Organization/{org}"}}
    )
    assert hs in _ids(
        (
            await client.get(BASE + "/", params={"organization": f"Organization/{org}"})
        ).json()
    )
    resp = await client.patch(f"{BASE}/{hs}", json={"providedBy": None})
    assert "providedBy" not in resp.json()
    assert hs not in _ids(
        (
            await client.get(BASE + "/", params={"organization": f"Organization/{org}"})
        ).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    hs = await create_healthcare_service(client, FULL)
    resp = await client.patch(
        f"{BASE}/{hs}", json={"location": [{"reference": "Location/999999"}]}
    )
    assert resp.status_code == 422
    assert "location" not in (await client.get(f"{BASE}/{hs}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    hs = await create_healthcare_service(client, FULL)
    resp = await client.patch(
        f"{BASE}/{hs}", json={"availableTime": [{"daysOfWeek": ["funday"]}]}
    )
    assert resp.status_code == 422
    assert (await client.get(f"{BASE}/{hs}")).json()["availableTime"][0][
        "daysOfWeek"
    ] == ["mon", "tue"]


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"active": False})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client):
    hs = await create_healthcare_service(client, FULL)
    assert (await client.delete(f"{BASE}/{hs}")).status_code == 204
    assert (await client.get(f"{BASE}/{hs}")).status_code == 404
    # Its index rows are gone with it.
    assert hs not in _ids(
        (await client.get(BASE + "/", params={"name": "Cardiology"})).json()
    )
    assert hs not in _ids(
        (await client.get(BASE + "/", params={"specialty": "394579002"})).json()
    )


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client):
    _as_user(permissions=["healthcare_service:read"])
    assert (await client.post(BASE + "/", json=MINIMAL)).status_code == 403


async def test_org_less_token_rejected(client):
    hs = await create_healthcare_service(client)

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=MINIMAL)).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{hs}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    hs = await create_healthcare_service(client)
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{hs}"),
            await other_client.patch(f"{BASE}/{hs}", json={"active": False}),
            await other_client.delete(f"{BASE}/{hs}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_healthcare_service(client, {"name": "TenantAOnly Clinic"})
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"name": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
        assert "entry" not in bundle
    finally:
        _as_user()

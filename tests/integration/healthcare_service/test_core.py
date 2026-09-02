"""Core healthcare_service endpoint coverage.

HealthcareService follows Organization's "set once, rarely edited" shape —
5 endpoints (create/get/patch/list/delete), no sub-resource routes and no
/me route. Every supplied sub-resource list on create/patch (identifier,
category, type, specialty, location, telecom, coverageArea,
serviceProvisionCode, eligibility, program, characteristic, communication,
referralMethod, availableTime, notAvailable, endpoint) replaces the
corresponding rows wholesale. Same JWT/RBAC auth rollout as Organization:
org_id/created_by/updated_by come from the verified token, never the body.

This file holds:
- create (minimal + full nested payload, FHIR format, validation,
  providedBy/location reference resolution + rejection)
- read (plain + FHIR, not found)
- list (plain, FHIR bundle, pagination, every Medplum-mirrored filter, sort)
- patch (field updates, sub-resource list replace, not found)
- delete
- auth: org-less token, missing permission scope, cross-org isolation
"""

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import (
    assert_fhir_bundle,
    assert_fhir_healthcare_service,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_healthcare_service,
)
from tests.integration.healthcare_service.support import (
    BASE,
    FHIR_ACCEPT,
    FULL,
    MINIMAL,
    create_healthcare_service,
    seed_location,
)
from tests.integration.organization.support import (
    BASE as ORG_BASE,
    MINIMAL as ORG_MINIMAL,
)

HS_PERMS = [
    "healthcare_service:create",
    "healthcare_service:read",
    "healthcare_service:update",
    "healthcare_service:delete",
]
ORG_AND_HS_PERMS = HS_PERMS + [
    "organization:create",
    "organization:read",
    "organization:update",
    "organization:delete",
]


async def _create_organization(client, name="Provider Org") -> int:
    resp = await client.post(ORG_BASE + "/", json={**ORG_MINIMAL, "name": name})
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_healthcare_service_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200
    assert_plain_healthcare_service(resp.json(), name="Test Healthcare Service", active=True)


async def test_create_healthcare_service_full(client):
    resp = await client.post(BASE + "/", json=FULL)
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_healthcare_service(data, name="Cardiology Services", active=True)
    assert data["identifier"][0]["value"] == "HS-1001"
    assert data["identifier"][0]["assigner_identifier_value"] == "EXTERNAL-1"
    assert data["category"][0]["coding_code"] == "8"
    assert data["type"][0]["coding_code"] == "394579002"
    assert data["specialty"][0]["coding_code"] == "394579002"
    assert data["telecom"][0]["value"] == "555-1234"
    assert data["location"][0]["reference_identifier_value"] == "LOC-9"
    assert data["coverage_area"][0]["reference_identifier_value"] == "LOC-8"
    assert data["service_provision_code"][0]["coding_code"] == "free"
    assert data["eligibility"][0]["code_code"] == "ind"
    assert data["program"][0]["coding_code"] == "mh"
    assert data["characteristic"][0]["coding_code"] == "wheelchair"
    assert data["communication"][0]["coding_code"] == "en"
    assert data["referral_method"][0]["coding_code"] == "phone"
    assert data["available_time"][0]["days_of_week"] == ["mon", "tue", "wed", "thu", "fri"]
    assert data["available_time"][0]["available_start_time"] == "09:00:00"
    assert data["not_available"][0]["description"] == "Closed for renovations."
    assert data["endpoint"][0]["reference_identifier_value"] == "EP-1"


async def test_create_healthcare_service_returns_fhir_format(client):
    resp = await client.post(BASE + "/", json=MINIMAL, headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert "application/fhir+json" in resp.headers["content-type"]
    assert_fhir_healthcare_service(resp.json(), name="Test Healthcare Service")


async def test_create_healthcare_service_extra_field_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "nonexistent_field": "value"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_healthcare_service_org_id_in_body_rejected(client):
    """org_id/created_by/updated_by come from the verified token — not
    request-body fields — since HealthcareService's JWT/RBAC rollout."""
    resp = await client.post(BASE + "/", json={**MINIMAL, "org_id": "sneaky-org"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_healthcare_service_created_by_derived_from_actor(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200
    data = resp.json()
    assert data["created_by"] == "u-test"
    assert data["org_id"] == "org-test"


async def test_create_healthcare_service_with_provided_by(client):
    """providedBy is a real cross-resource reference (Reference(Organization))
    validated for existence at write time — Organization is mounted in this
    test env (see configs/config.yaml), so create a real one via its API."""
    app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_AND_HS_PERMS)
    org_id = await _create_organization(client)
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "provided_by": f"Organization/{org_id}"}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["provided_by_id"] == org_id
    assert data["provided_by"] == f"Organization/{org_id}"


async def test_create_healthcare_service_nonexistent_provided_by_rejected(client):
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "provided_by": "Organization/9999999"}
    )
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_healthcare_service_with_resolved_location(client, _engine):
    """location[] is a real cross-resource reference (Reference(Location))
    validated for existence at write time. Location's own router isn't
    mounted in this test env, so seed a row directly."""
    location_id = await seed_location(_engine)
    resp = await client.post(
        BASE + "/",
        json={**MINIMAL, "location": [{"reference": f"Location/{location_id}"}]},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["location"][0]["reference_id"] == location_id
    assert data["location"][0]["reference"] == f"Location/{location_id}"


async def test_create_healthcare_service_nonexistent_location_rejected(client):
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "location": [{"reference": "Location/9999999"}]}
    )
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_healthcare_service_nonexistent_coverage_area_rejected(client):
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "coverage_area": [{"reference": "Location/9999999"}]}
    )
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


# ── Get ──────────────────────────────────────────────────────────────────────


async def test_get_healthcare_service_by_id_plain(client):
    hs_id = await create_healthcare_service(client)
    resp = await client.get(f"{BASE}/{hs_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_healthcare_service(data, name="Test Healthcare Service")
    assert data["id"] == hs_id


async def test_get_healthcare_service_by_id_fhir(client):
    hs_id = await create_healthcare_service(client)
    resp = await client.get(f"{BASE}/{hs_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert_fhir_healthcare_service(resp.json())
    assert resp.json()["id"] == str(hs_id)


async def test_get_healthcare_service_not_found(client):
    resp = await client.get(f"{BASE}/9999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────────


async def test_list_healthcare_services_plain(client):
    await create_healthcare_service(client)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200
    assert_paginated(resp.json())


async def test_list_healthcare_services_fhir_bundle(client):
    await create_healthcare_service(client)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert_fhir_bundle(resp.json())


async def test_list_healthcare_services_pagination(client):
    for i in range(3):
        await create_healthcare_service(client, {**MINIMAL, "name": f"Service {i}"})
    resp = await client.get(f"{BASE}/?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) <= 2
    assert data["limit"] == 2


async def test_list_healthcare_services_filter_active(client):
    await create_healthcare_service(client, {**MINIMAL, "name": "Active Svc", "active": True})
    await create_healthcare_service(client, {**MINIMAL, "name": "Inactive Svc", "active": False})
    resp = await client.get(BASE + "/", params={"active": "false"})
    assert resp.status_code == 200
    assert all(hs["active"] is False for hs in resp.json()["data"])


async def test_list_healthcare_services_filter_name(client):
    await create_healthcare_service(client, {**MINIMAL, "name": "FindMeByName"})
    resp = await client.get(BASE + "/", params={"name": "FindMeByName"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_healthcare_services_filter_identifier(client):
    await create_healthcare_service(client, FULL)
    resp = await client.get(BASE + "/", params={"identifier": "HS-1001"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_healthcare_services_filter_service_category(client):
    await create_healthcare_service(client, FULL)
    resp = await client.get(BASE + "/", params={"service-category": "8"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_healthcare_services_filter_service_type(client):
    await create_healthcare_service(client, FULL)
    resp = await client.get(BASE + "/", params={"service-type": "394579002"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_healthcare_services_filter_specialty(client):
    await create_healthcare_service(client, FULL)
    resp = await client.get(BASE + "/", params={"specialty": "394579002"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_healthcare_services_filter_characteristic(client):
    await create_healthcare_service(client, FULL)
    resp = await client.get(BASE + "/", params={"characteristic": "wheelchair"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_healthcare_services_filter_program(client):
    await create_healthcare_service(client, FULL)
    resp = await client.get(BASE + "/", params={"program": "mh"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_healthcare_services_filter_organization(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_AND_HS_PERMS)
    org_id = await _create_organization(client)
    await create_healthcare_service(
        client, {**MINIMAL, "provided_by": f"Organization/{org_id}"}
    )
    resp = await client.get(BASE + "/", params={"organization": f"Organization/{org_id}"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_healthcare_services_sort_and_total_mode_none(client):
    await create_healthcare_service(client)
    resp = await client.get(BASE + "/", params={"sort": "-name", "total_mode": "none"})
    assert resp.status_code == 200
    assert resp.json()["total"] is None


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_healthcare_service_name(client):
    hs_id = await create_healthcare_service(client)
    resp = await client.patch(f"{BASE}/{hs_id}", json={"name": "Updated Service"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Service"
    assert data["updated_by"] == "u-test"


async def test_patch_healthcare_service_active(client):
    hs_id = await create_healthcare_service(client)
    resp = await client.patch(f"{BASE}/{hs_id}", json={"active": False})
    assert resp.status_code == 200
    assert resp.json()["active"] is False


async def test_patch_healthcare_service_replaces_category_list(client):
    hs_id = await create_healthcare_service(client, FULL)
    resp = await client.patch(
        f"{BASE}/{hs_id}",
        json={"category": [{"coding_code": "new-cat", "coding_display": "New Category"}]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["category"]) == 1
    assert data["category"][0]["coding_code"] == "new-cat"
    # Untouched lists are left alone.
    assert len(data["identifier"]) == 1


async def test_patch_healthcare_service_provided_by_resolved(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_AND_HS_PERMS)
    org_id = await _create_organization(client)
    hs_id = await create_healthcare_service(client)
    resp = await client.patch(
        f"{BASE}/{hs_id}", json={"provided_by": f"Organization/{org_id}"}
    )
    assert resp.status_code == 200
    assert resp.json()["provided_by_id"] == org_id


async def test_patch_healthcare_service_not_found(client):
    resp = await client.patch(f"{BASE}/9999999", json={"name": "X"})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete_healthcare_service(client):
    hs_id = await create_healthcare_service(client)
    resp = await client.delete(f"{BASE}/{hs_id}")
    assert resp.status_code == 204
    assert (await client.get(f"{BASE}/{hs_id}")).status_code == 404


async def test_delete_healthcare_service_not_found(client):
    resp = await client.delete(f"{BASE}/9999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Auth & tenancy ───────────────────────────────────────────────────────────


async def test_create_healthcare_service_no_permission(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=["healthcare_service:read"])
    try:
        resp = await client.post(BASE + "/", json=MINIMAL)
        assert_operation_outcome(resp.json(), expected_status=403, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=HS_PERMS)


async def test_create_healthcare_service_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(org_id=None, permissions=HS_PERMS)
    try:
        resp = await client.post(BASE + "/", json=MINIMAL)
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=HS_PERMS)


async def test_list_healthcare_services_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(org_id=None, permissions=HS_PERMS)
    try:
        resp = await client.get(BASE + "/")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=HS_PERMS)


async def test_get_healthcare_service_org_mismatch_returns_404(client, other_client):
    # Requesting other_client overwrote the get_current_user override with its
    # own default identity — restore org-test's healthcare_service permissions
    # before creating, then switch to org-other before the read.
    app.dependency_overrides[get_current_user] = make_test_user(permissions=HS_PERMS)
    hs_id = await create_healthcare_service(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=HS_PERMS
    )
    try:
        resp = await other_client.get(f"{BASE}/{hs_id}")
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=HS_PERMS)


async def test_patch_healthcare_service_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=HS_PERMS)
    hs_id = await create_healthcare_service(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=HS_PERMS
    )
    try:
        resp = await other_client.patch(f"{BASE}/{hs_id}", json={"name": "Hacked"})
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=HS_PERMS)


async def test_delete_healthcare_service_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=HS_PERMS)
    hs_id = await create_healthcare_service(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=HS_PERMS
    )
    try:
        resp = await other_client.delete(f"{BASE}/{hs_id}")
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=HS_PERMS)


async def test_list_healthcare_services_cross_tenant_isolation(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=HS_PERMS)
    await create_healthcare_service(client, {**MINIMAL, "name": "Tenant-A-Only-Service"})
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=HS_PERMS
    )
    try:
        resp = await other_client.get(BASE + "/", params={"name": "Tenant-A-Only-Service"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=HS_PERMS)

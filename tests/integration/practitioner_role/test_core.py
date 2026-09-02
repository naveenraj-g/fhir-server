"""Core practitioner_role endpoint coverage.

PractitionerRole follows Organization/HealthcareService's "set once, rarely
edited" shape — 5 endpoints (create/get/patch/list/delete), no sub-resource
routes and no /me route. Every supplied sub-resource list on create/patch
(identifier, code, specialty, location, healthcareService, telecom,
availableTime, notAvailable, endpoint) replaces the corresponding rows
wholesale. Same JWT/RBAC auth rollout as Organization/HealthcareService:
org_id/created_by/updated_by come from the verified token, never the body.

This file holds:
- create (minimal + full nested payload, FHIR format, validation,
  practitioner/organization/location/healthcareService reference
  resolution + rejection)
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
    assert_fhir_practitioner_role,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_practitioner_role,
)
from tests.integration.organization.support import (
    BASE as ORG_BASE,
    MINIMAL as ORG_MINIMAL,
)
from tests.integration.practitioner_role.support import (
    BASE,
    FHIR_ACCEPT,
    FULL,
    MINIMAL,
    create_practitioner_role,
    seed_location,
    seed_practitioner,
)

PR_PERMS = [
    "practitioner_role:create",
    "practitioner_role:read",
    "practitioner_role:update",
    "practitioner_role:delete",
]
ORG_AND_PR_PERMS = PR_PERMS + [
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


async def test_create_practitioner_role_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200
    assert_plain_practitioner_role(resp.json(), active=True)


async def test_create_practitioner_role_full(client):
    resp = await client.post(BASE + "/", json=FULL)
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_practitioner_role(data, active=True)
    assert data["identifier"][0]["value"] == "PR-1001"
    assert data["identifier"][0]["assigner_identifier_value"] == "EXTERNAL-1"
    assert data["code"][0]["coding_code"] == "59058001"
    assert data["specialty"][0]["coding_code"] == "394814009"
    assert data["location"][0]["reference_identifier_value"] == "LOC-9"
    assert data["healthcare_service"][0]["reference_identifier_value"] == "HS-9"
    assert data["telecom"][0]["value"] == "555-1234"
    assert data["available_time"][0]["days_of_week"] == ["mon", "tue", "wed", "thu", "fri"]
    assert data["available_time"][0]["available_start_time"] == "09:00:00"
    assert data["not_available"][0]["description"] == "Annual leave."
    assert data["endpoint"][0]["reference_identifier_value"] == "EP-1"


async def test_create_practitioner_role_returns_fhir_format(client):
    resp = await client.post(BASE + "/", json=MINIMAL, headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert "application/fhir+json" in resp.headers["content-type"]
    assert_fhir_practitioner_role(resp.json())


async def test_create_practitioner_role_extra_field_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "nonexistent_field": "value"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_practitioner_role_org_id_in_body_rejected(client):
    """org_id/created_by/updated_by come from the verified token — not
    request-body fields — since PractitionerRole's JWT/RBAC rollout."""
    resp = await client.post(BASE + "/", json={**MINIMAL, "org_id": "sneaky-org"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_practitioner_role_created_by_derived_from_actor(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200
    data = resp.json()
    assert data["created_by"] == "u-test"
    assert data["org_id"] == "org-test"


async def test_create_practitioner_role_with_organization(client):
    """organization is a real cross-resource reference (Reference(Organization))
    validated for existence at write time — Organization is mounted in this
    test env (see configs/config.yaml), so create a real one via its API."""
    app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_AND_PR_PERMS)
    org_id = await _create_organization(client)
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "organization": f"Organization/{org_id}"}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["organization_id"] == org_id
    assert data["organization"] == f"Organization/{org_id}"


async def test_create_practitioner_role_nonexistent_organization_rejected(client):
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "organization": "Organization/9999999"}
    )
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_practitioner_role_with_resolved_practitioner(client, _engine):
    """practitioner is a real cross-resource reference (Reference(Practitioner))
    validated for existence at write time. Practitioner's own router isn't
    mounted in this test env, so seed a row directly."""
    practitioner_id = await seed_practitioner(_engine)
    resp = await client.post(
        BASE + "/",
        json={**MINIMAL, "practitioner": f"Practitioner/{practitioner_id}"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["practitioner_id"] == practitioner_id
    assert data["practitioner"] == f"Practitioner/{practitioner_id}"


async def test_create_practitioner_role_nonexistent_practitioner_rejected(client):
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "practitioner": "Practitioner/9999999"}
    )
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_practitioner_role_with_resolved_location(client, _engine):
    location_id = await seed_location(_engine)
    resp = await client.post(
        BASE + "/",
        json={**MINIMAL, "location": [{"reference": f"Location/{location_id}"}]},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["location"][0]["reference_id"] == location_id
    assert data["location"][0]["reference"] == f"Location/{location_id}"


async def test_create_practitioner_role_nonexistent_location_rejected(client):
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "location": [{"reference": "Location/9999999"}]}
    )
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_practitioner_role_nonexistent_healthcare_service_rejected(client):
    resp = await client.post(
        BASE + "/",
        json={**MINIMAL, "healthcare_service": [{"reference": "HealthcareService/9999999"}]},
    )
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


# ── Get ──────────────────────────────────────────────────────────────────────


async def test_get_practitioner_role_by_id_plain(client):
    pr_id = await create_practitioner_role(client)
    resp = await client.get(f"{BASE}/{pr_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_practitioner_role(data)
    assert data["id"] == pr_id


async def test_get_practitioner_role_by_id_fhir(client):
    pr_id = await create_practitioner_role(client)
    resp = await client.get(f"{BASE}/{pr_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert_fhir_practitioner_role(resp.json())
    assert resp.json()["id"] == str(pr_id)


async def test_get_practitioner_role_not_found(client):
    resp = await client.get(f"{BASE}/9999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────────


async def test_list_practitioner_roles_plain(client):
    await create_practitioner_role(client)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200
    assert_paginated(resp.json())


async def test_list_practitioner_roles_fhir_bundle(client):
    await create_practitioner_role(client)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert_fhir_bundle(resp.json())


async def test_list_practitioner_roles_pagination(client):
    for _ in range(3):
        await create_practitioner_role(client)
    resp = await client.get(f"{BASE}/?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) <= 2
    assert data["limit"] == 2


async def test_list_practitioner_roles_filter_active(client):
    await create_practitioner_role(client, {**MINIMAL, "active": True})
    await create_practitioner_role(client, {**MINIMAL, "active": False})
    resp = await client.get(BASE + "/", params={"active": "false"})
    assert resp.status_code == 200
    assert all(pr["active"] is False for pr in resp.json()["data"])


async def test_list_practitioner_roles_filter_identifier(client):
    await create_practitioner_role(client, FULL)
    resp = await client.get(BASE + "/", params={"identifier": "PR-1001"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_practitioner_roles_filter_role(client):
    await create_practitioner_role(client, FULL)
    resp = await client.get(BASE + "/", params={"role": "59058001"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_practitioner_roles_filter_specialty(client):
    await create_practitioner_role(client, FULL)
    resp = await client.get(BASE + "/", params={"specialty": "394814009"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_practitioner_roles_filter_email(client):
    await create_practitioner_role(
        client, {**MINIMAL, "telecom": [{"system": "email", "value": "doc@example.com"}]}
    )
    resp = await client.get(BASE + "/", params={"email": "doc@example.com"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_practitioner_roles_filter_phone(client):
    await create_practitioner_role(client, FULL)
    resp = await client.get(BASE + "/", params={"phone": "555-1234"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_practitioner_roles_filter_telecom(client):
    await create_practitioner_role(client, FULL)
    resp = await client.get(BASE + "/", params={"telecom": "555-1234"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_practitioner_roles_filter_organization(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_AND_PR_PERMS)
    org_id = await _create_organization(client)
    await create_practitioner_role(
        client, {**MINIMAL, "organization": f"Organization/{org_id}"}
    )
    resp = await client.get(BASE + "/", params={"organization": f"Organization/{org_id}"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_practitioner_roles_filter_practitioner(client, _engine):
    practitioner_id = await seed_practitioner(_engine)
    await create_practitioner_role(
        client, {**MINIMAL, "practitioner": f"Practitioner/{practitioner_id}"}
    )
    resp = await client.get(
        BASE + "/", params={"practitioner": f"Practitioner/{practitioner_id}"}
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_practitioner_roles_filter_date(client):
    await create_practitioner_role(
        client,
        {**MINIMAL, "period_start": "2024-01-01T00:00:00Z", "period_end": "2024-12-31T00:00:00Z"},
    )
    resp = await client.get(BASE + "/", params={"date": "2024-06-15"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
    resp_outside = await client.get(BASE + "/", params={"date": "2020-01-01"})
    assert resp_outside.status_code == 200


async def test_list_practitioner_roles_sort_and_total_mode_none(client):
    await create_practitioner_role(client)
    resp = await client.get(BASE + "/", params={"sort": "-created_at", "total_mode": "none"})
    assert resp.status_code == 200
    assert resp.json()["total"] is None


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_practitioner_role_active(client):
    pr_id = await create_practitioner_role(client)
    resp = await client.patch(f"{BASE}/{pr_id}", json={"active": False})
    assert resp.status_code == 200
    data = resp.json()
    assert data["active"] is False
    assert data["updated_by"] == "u-test"


async def test_patch_practitioner_role_replaces_code_list(client):
    pr_id = await create_practitioner_role(client, FULL)
    resp = await client.patch(
        f"{BASE}/{pr_id}",
        json={"code": [{"coding_code": "new-code", "coding_display": "New Role"}]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["code"]) == 1
    assert data["code"][0]["coding_code"] == "new-code"
    # Untouched lists are left alone.
    assert len(data["identifier"]) == 1


async def test_patch_practitioner_role_organization_resolved(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_AND_PR_PERMS)
    org_id = await _create_organization(client)
    pr_id = await create_practitioner_role(client)
    resp = await client.patch(
        f"{BASE}/{pr_id}", json={"organization": f"Organization/{org_id}"}
    )
    assert resp.status_code == 200
    assert resp.json()["organization_id"] == org_id


async def test_patch_practitioner_role_not_found(client):
    resp = await client.patch(f"{BASE}/9999999", json={"active": False})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete_practitioner_role(client):
    pr_id = await create_practitioner_role(client)
    resp = await client.delete(f"{BASE}/{pr_id}")
    assert resp.status_code == 204
    assert (await client.get(f"{BASE}/{pr_id}")).status_code == 404


async def test_delete_practitioner_role_not_found(client):
    resp = await client.delete(f"{BASE}/9999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Auth & tenancy ───────────────────────────────────────────────────────────


async def test_create_practitioner_role_no_permission(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=["practitioner_role:read"])
    try:
        resp = await client.post(BASE + "/", json=MINIMAL)
        assert_operation_outcome(resp.json(), expected_status=403, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=PR_PERMS)


async def test_create_practitioner_role_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(org_id=None, permissions=PR_PERMS)
    try:
        resp = await client.post(BASE + "/", json=MINIMAL)
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=PR_PERMS)


async def test_list_practitioner_roles_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(org_id=None, permissions=PR_PERMS)
    try:
        resp = await client.get(BASE + "/")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=PR_PERMS)


async def test_get_practitioner_role_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=PR_PERMS)
    pr_id = await create_practitioner_role(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=PR_PERMS
    )
    try:
        resp = await other_client.get(f"{BASE}/{pr_id}")
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=PR_PERMS)


async def test_patch_practitioner_role_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=PR_PERMS)
    pr_id = await create_practitioner_role(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=PR_PERMS
    )
    try:
        resp = await other_client.patch(f"{BASE}/{pr_id}", json={"active": False})
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=PR_PERMS)


async def test_delete_practitioner_role_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=PR_PERMS)
    pr_id = await create_practitioner_role(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=PR_PERMS
    )
    try:
        resp = await other_client.delete(f"{BASE}/{pr_id}")
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=PR_PERMS)


async def test_list_practitioner_roles_cross_tenant_isolation(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=PR_PERMS)
    await create_practitioner_role(client, {**MINIMAL, "availability_exceptions": "Tenant A only"})
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=PR_PERMS
    )
    try:
        resp = await other_client.get(BASE + "/")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=PR_PERMS)

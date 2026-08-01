"""Core organization endpoint coverage.

Organization is a "set once, rarely edited" resource — unlike Patient/
Practitioner it has exactly 5 endpoints (create/get/patch/list/delete), no
sub-resource routes and no /me route. Every supplied sub-resource list on
create/patch (identifier, type, alias, telecom, address, contact, endpoint)
replaces the corresponding rows wholesale.

This file holds:
- create (minimal + full nested payload, FHIR format, validation)
- read (plain + FHIR, not found)
- list (plain, FHIR bundle, pagination, every Medplum-mirrored filter, sort)
- patch (field updates, partOf hierarchy business rule, not found)
- delete
- auth: org-less token, missing permission scope, cross-org isolation
"""

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import (
    assert_fhir_bundle,
    assert_fhir_organization,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_organization,
)
from tests.integration.organization.support import BASE, FHIR_ACCEPT, FULL, MINIMAL, create_organization

ORG_PERMS = [
    "organization:create",
    "organization:read",
    "organization:update",
    "organization:delete",
]


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_organization_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200
    assert_plain_organization(resp.json(), name="Test Hospital", active=True)


async def test_create_organization_full(client):
    resp = await client.post(BASE + "/", json=FULL)
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_organization(data, name="General Hospital", active=True)
    assert data["identifier"][0]["value"] == "1234567893"
    assert data["identifier"][0]["assigner_identifier_value"] == "EXTERNAL-1"
    assert data["type"][0]["coding_code"] == "prov"
    assert data["alias"][0]["value"] == "Gen Hosp"
    assert data["telecom"][0]["value"] == "555-1234"
    assert data["address"][0]["city"] == "Anytown"
    assert data["contact"][0]["name_family"] == "Smith"
    assert len(data["contact"][0]["telecoms"]) == 1
    assert data["endpoint"][0]["reference_identifier_value"] == "EP-1"


async def test_create_organization_returns_fhir_format(client):
    resp = await client.post(BASE + "/", json=MINIMAL, headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert "application/fhir+json" in resp.headers["content-type"]
    assert_fhir_organization(resp.json(), name="Test Hospital")


async def test_create_organization_extra_field_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "nonexistent_field": "value"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_organization_org_id_in_body_rejected(client):
    """org_id/created_by/updated_by come from the verified token — not
    request-body fields — since Organization's JWT/RBAC rollout."""
    resp = await client.post(BASE + "/", json={**MINIMAL, "org_id": "sneaky-org"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_organization_created_by_derived_from_actor(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200
    data = resp.json()
    assert data["created_by"] == "u-test"
    assert data["org_id"] == "org-test"


async def test_create_organization_with_partof(client):
    parent_id = await create_organization(client, {**MINIMAL, "name": "Parent Org"})
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "name": "Child Org", "partof": f"Organization/{parent_id}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["partof_id"] == parent_id


async def test_create_organization_nonexistent_partof_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "partof": "Organization/9999999"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


# ── Get ──────────────────────────────────────────────────────────────────────


async def test_get_organization_by_id_plain(client):
    org_id = await create_organization(client)
    resp = await client.get(f"{BASE}/{org_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_organization(data, name="Test Hospital")
    assert data["id"] == org_id


async def test_get_organization_by_id_fhir(client):
    org_id = await create_organization(client)
    resp = await client.get(f"{BASE}/{org_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert_fhir_organization(resp.json())
    assert resp.json()["id"] == str(org_id)


async def test_get_organization_fhir_partof_reference(client):
    parent_id = await create_organization(client, {**MINIMAL, "name": "Parent Org"})
    child_id = await create_organization(
        client, {**MINIMAL, "name": "Child Org", "partof": f"Organization/{parent_id}"}
    )
    resp = await client.get(f"{BASE}/{child_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert resp.json()["partOf"]["reference"] == f"Organization/{parent_id}"


async def test_get_organization_not_found(client):
    resp = await client.get(f"{BASE}/9999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────────


async def test_list_organizations_plain(client):
    await create_organization(client)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200
    assert_paginated(resp.json())


async def test_list_organizations_fhir_bundle(client):
    await create_organization(client)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert_fhir_bundle(resp.json())


async def test_list_organizations_pagination(client):
    for i in range(3):
        await create_organization(client, {**MINIMAL, "name": f"Org {i}"})
    resp = await client.get(f"{BASE}/?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) <= 2
    assert data["limit"] == 2


async def test_list_organizations_filter_active(client):
    await create_organization(client, {**MINIMAL, "name": "Active Org", "active": True})
    await create_organization(client, {**MINIMAL, "name": "Inactive Org", "active": False})
    resp = await client.get(BASE + "/", params={"active": "false"})
    assert resp.status_code == 200
    assert all(o["active"] is False for o in resp.json()["data"])


async def test_list_organizations_filter_name_matches_alias(client):
    await create_organization(
        client, {**MINIMAL, "name": "Unrelated Name", "alias": [{"value": "FindMeAlias"}]}
    )
    resp = await client.get(BASE + "/", params={"name": "FindMeAlias"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_organizations_filter_identifier(client):
    await create_organization(client, FULL)
    resp = await client.get(BASE + "/", params={"identifier": "1234567893"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_organizations_filter_type(client):
    await create_organization(client, FULL)
    resp = await client.get(BASE + "/", params={"type": "prov"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_organizations_filter_address_city(client):
    await create_organization(client, FULL)
    resp = await client.get(BASE + "/", params={"address-city": "Anytown"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_organizations_filter_partof(client):
    parent_id = await create_organization(client, {**MINIMAL, "name": "Parent Org"})
    child_id = await create_organization(
        client, {**MINIMAL, "name": "Child Org", "partof": f"Organization/{parent_id}"}
    )
    resp = await client.get(BASE + "/", params={"partof": f"Organization/{parent_id}"})
    assert resp.status_code == 200
    assert {o["id"] for o in resp.json()["data"]} == {child_id}


async def test_list_organizations_sort_and_total_mode_none(client):
    await create_organization(client)
    resp = await client.get(BASE + "/", params={"sort": "-name", "total_mode": "none"})
    assert resp.status_code == 200
    assert resp.json()["total"] is None


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_organization_name(client):
    org_id = await create_organization(client)
    resp = await client.patch(f"{BASE}/{org_id}", json={"name": "Updated Hospital"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Hospital"
    assert data["updated_by"] == "u-test"


async def test_patch_organization_active(client):
    org_id = await create_organization(client)
    resp = await client.patch(f"{BASE}/{org_id}", json={"active": False})
    assert resp.status_code == 200
    assert resp.json()["active"] is False


async def test_patch_organization_replaces_alias_list(client):
    org_id = await create_organization(client, FULL)
    resp = await client.patch(f"{BASE}/{org_id}", json={"alias": [{"value": "New Alias"}]})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["alias"]) == 1
    assert data["alias"][0]["value"] == "New Alias"
    # Untouched lists are left alone.
    assert len(data["identifier"]) == 1


async def test_patch_organization_partof_resolved(client):
    parent_id = await create_organization(client, {**MINIMAL, "name": "Parent Org"})
    child_id = await create_organization(client, {**MINIMAL, "name": "Child Org"})
    resp = await client.patch(f"{BASE}/{child_id}", json={"partof": f"Organization/{parent_id}"})
    assert resp.status_code == 200
    assert resp.json()["partof_id"] == parent_id


async def test_patch_organization_partof_cycle_rejected(client):
    parent_id = await create_organization(client, {**MINIMAL, "name": "Parent Org"})
    child_id = await create_organization(
        client, {**MINIMAL, "name": "Child Org", "partof": f"Organization/{parent_id}"}
    )
    resp = await client.patch(f"{BASE}/{parent_id}", json={"partof": f"Organization/{child_id}"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_patch_organization_partof_self_reference_rejected(client):
    org_id = await create_organization(client)
    resp = await client.patch(f"{BASE}/{org_id}", json={"partof": f"Organization/{org_id}"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_patch_organization_not_found(client):
    resp = await client.patch(f"{BASE}/9999999", json={"name": "X"})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete_organization(client):
    org_id = await create_organization(client)
    resp = await client.delete(f"{BASE}/{org_id}")
    assert resp.status_code == 204
    assert (await client.get(f"{BASE}/{org_id}")).status_code == 404


async def test_delete_organization_not_found(client):
    resp = await client.delete(f"{BASE}/9999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Auth & tenancy ───────────────────────────────────────────────────────────


async def test_create_organization_no_permission(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=["organization:read"])
    try:
        resp = await client.post(BASE + "/", json=MINIMAL)
        assert_operation_outcome(resp.json(), expected_status=403, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)


async def test_create_organization_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(org_id=None, permissions=ORG_PERMS)
    try:
        resp = await client.post(BASE + "/", json=MINIMAL)
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)


async def test_list_organizations_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(org_id=None, permissions=ORG_PERMS)
    try:
        resp = await client.get(BASE + "/")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)


async def test_get_organization_org_mismatch_returns_404(client, other_client):
    # Requesting other_client overwrote the get_current_user override with its
    # own (patient-scoped) default identity — restore org-test's organization
    # permissions before creating, then switch to org-other before the read.
    app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)
    org_id = await create_organization(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=ORG_PERMS
    )
    try:
        resp = await other_client.get(f"{BASE}/{org_id}")
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)


async def test_patch_organization_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)
    org_id = await create_organization(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=ORG_PERMS
    )
    try:
        resp = await other_client.patch(f"{BASE}/{org_id}", json={"name": "Hacked"})
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)


async def test_delete_organization_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)
    org_id = await create_organization(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=ORG_PERMS
    )
    try:
        resp = await other_client.delete(f"{BASE}/{org_id}")
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)


async def test_list_organizations_cross_tenant_isolation(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)
    await create_organization(client, {**MINIMAL, "name": "Tenant-A-Only-Org"})
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=ORG_PERMS
    )
    try:
        resp = await other_client.get(BASE + "/", params={"name": "Tenant-A-Only-Org"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)

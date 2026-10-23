"""Core practitioner endpoint coverage.

Practitioner has 6 endpoints (create/get/patch/list/delete/me), no
sub-resource routes. Every supplied sub-resource list on create/patch
(identifier, name, telecom, address, photo, qualification, communication)
replaces the corresponding rows wholesale. Unlike Organization/Location/
HealthcareService, Practitioner keeps `user_id` and a `/me` route — see
PractitionerModel's docstring.

This file holds:
- create (minimal + full nested payload, FHIR format, validation)
- read (plain + FHIR, not found)
- patch (field updates, sub-list replace, not found)
- list (plain, FHIR bundle, filters)
- /me (scoped to user_id)
- delete
- auth: cross-org isolation
"""

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import (
    assert_fhir_bundle,
    assert_fhir_practitioner,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_practitioner,
)
from tests.integration.practitioner.support import BASE, FHIR_ACCEPT, FULL, MINIMAL, create_practitioner

PRACTITIONER_PERMS = [
    "practitioner:create",
    "practitioner:read",
    "practitioner:update",
    "practitioner:delete",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_practitioner_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200, resp.text
    assert_plain_practitioner(resp.json(), active=True)
    assert resp.json()["name"][0]["family"] == "Careful"


async def test_create_practitioner_full(client):
    resp = await client.post(BASE + "/", json=FULL)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_practitioner(data, active=True, gender="male", user_id="end-user-1")
    assert data["identifier"][0]["value"] == "9941339108"
    assert data["identifier"][0]["type_codings"][0]["code"] == "NPI"
    assert data["name"][0]["family"] == "Careful"
    assert data["telecom"][0]["value"] == "555-9988"
    assert data["address"][0]["city"] == "PleasantVille"
    assert data["photo"][0]["url"] == "https://fhir-server.dev/fhir/assets/photo.png"
    assert data["qualification"][0]["code_codings"][0]["code"] == "BS"
    assert data["communication"][0]["codings"][0]["code"] == "en"


async def test_create_practitioner_returns_fhir_format(client):
    resp = await client.post(BASE + "/", json=MINIMAL, headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert "application/fhir+json" in resp.headers["content-type"]
    assert_fhir_practitioner(resp.json())
    assert resp.json()["name"][0]["family"] == "Careful"


async def test_create_practitioner_extra_field_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "nonexistent_field": "value"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_practitioner_tenant_id_in_body_rejected(client):
    """tenant_id/created_by/updated_by come from the verified token — not
    request-body fields — same as Organization/Location/HealthcareService."""
    resp = await client.post(BASE + "/", json={**MINIMAL, "tenant_id": "sneaky-org"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_practitioner_created_by_derived_from_actor(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200
    data = resp.json()
    assert data["created_by"] == "u-test"
    assert data["org_id"] == "org-test"


async def test_create_practitioner_nonexistent_qualification_issuer_rejected(client):
    payload = {
        **MINIMAL,
        "qualification": [{"code_text": "BS", "issuer": "Organization/999999"}],
    }
    resp = await client.post(BASE + "/", json=payload)
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_practitioner_plain(client):
    pid = await create_practitioner(client, FULL)
    resp = await client.get(f"{BASE}/{pid}")
    assert resp.status_code == 200
    assert_plain_practitioner(resp.json(), id=pid)


async def test_get_practitioner_fhir(client):
    pid = await create_practitioner(client, FULL)
    resp = await client.get(f"{BASE}/{pid}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert_fhir_practitioner(resp.json(), id=str(pid))


async def test_get_practitioner_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


async def test_get_practitioner_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=PRACTITIONER_PERMS)
    pid = await create_practitioner(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=PRACTITIONER_PERMS
    )
    try:
        resp = await other_client.get(f"{BASE}/{pid}")
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=PRACTITIONER_PERMS)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_practitioner_field(client):
    pid = await create_practitioner(client)
    resp = await client.patch(f"{BASE}/{pid}", json={"active": False})
    assert resp.status_code == 200
    assert resp.json()["active"] is False


async def test_patch_practitioner_replaces_name_list(client):
    pid = await create_practitioner(client, FULL)
    resp = await client.patch(
        f"{BASE}/{pid}", json={"name": [{"family": "Newname", "given": ["New"]}]}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["name"]) == 1
    assert data["name"][0]["family"] == "Newname"


async def test_patch_practitioner_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"active": False})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


async def test_patch_practitioner_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=PRACTITIONER_PERMS)
    pid = await create_practitioner(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=PRACTITIONER_PERMS
    )
    try:
        resp = await other_client.patch(f"{BASE}/{pid}", json={"active": False})
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=PRACTITIONER_PERMS)


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_practitioners_plain(client):
    await create_practitioner(client, {**MINIMAL, "name": [{"family": "ListTestFamily"}]})
    resp = await client.get(BASE + "/", params={"family": "ListTestFamily"})
    assert resp.status_code == 200
    assert_paginated(resp.json(), min_total=1)


async def test_list_practitioners_fhir_bundle(client):
    await create_practitioner(client, {**MINIMAL, "name": [{"family": "BundleTestFamily"}]})
    resp = await client.get(BASE + "/", params={"family": "BundleTestFamily"}, headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert_fhir_bundle(resp.json(), min_total=1)


async def test_list_practitioners_cross_tenant_isolation(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=PRACTITIONER_PERMS)
    await create_practitioner(client, {**MINIMAL, "name": [{"family": "Tenant-A-Only"}]})
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=PRACTITIONER_PERMS
    )
    try:
        resp = await other_client.get(BASE + "/", params={"family": "Tenant-A-Only"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=PRACTITIONER_PERMS)


# ── Me ───────────────────────────────────────────────────────────────────


async def test_list_my_practitioners_scoped_to_user_id(client):
    """`/me` scopes by the row's own `user_id` column matching the caller's
    identity (actor.sub, "u-test" for the `client` fixture) — not by
    `created_by`. A row whose `user_id` belongs to someone else must not
    appear, even though both rows were created by the same actor."""
    await create_practitioner(
        client, {**MINIMAL, "user_id": "u-test", "name": [{"family": "MineFamily"}]}
    )
    await create_practitioner(
        client, {**MINIMAL, "user_id": "someone-else", "name": [{"family": "NotMineFamily"}]}
    )
    resp = await client.get(BASE + "/me", params={"family": "MineFamily"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 1

    resp2 = await client.get(BASE + "/me", params={"family": "NotMineFamily"})
    assert resp2.status_code == 200
    assert resp2.json()["total"] == 0


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_practitioner(client):
    pid = await create_practitioner(client)
    resp = await client.delete(f"{BASE}/{pid}")
    assert resp.status_code == 204

    resp2 = await client.get(f"{BASE}/{pid}")
    assert_operation_outcome(resp2.json(), expected_status=404, response_status=resp2.status_code)


async def test_delete_practitioner_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


async def test_delete_practitioner_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=PRACTITIONER_PERMS)
    pid = await create_practitioner(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=PRACTITIONER_PERMS
    )
    try:
        resp = await other_client.delete(f"{BASE}/{pid}")
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=PRACTITIONER_PERMS)

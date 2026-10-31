"""Core group endpoint coverage.

Group has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
Every supplied sub-resource list on create/patch replaces corresponding rows wholesale.

This file holds:
- create (minimal + full nested payload, FHIR format, validation, reference check)
- read (plain + FHIR, not found)
- patch (field updates, sub-list replace, not found)
- list (plain, FHIR bundle, filters, pagination)
- delete
- auth: cross-org isolation and org-less rejection
"""

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import (
    assert_fhir_bundle,
    assert_fhir_group,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_group,
)
from tests.integration.group.support import (
    BASE,
    FHIR_ACCEPT,
    create_group,
    create_test_organization,
    create_test_patient,
    full_group,
    minimal_group,
)

GROUP_PERMS = [
    "group:create",
    "group:read",
    "group:update",
    "group:delete",
    "patient:create",
    "patient:read",
    "organization:create",
    "organization:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_group_minimal(client):
    resp = await client.post(BASE + "/", json=minimal_group())
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_group(data)
    assert data["type"] == "person"
    assert data["actual"] is True
    assert data["id"] >= 430000


async def test_create_group_full(client):
    p_id = await create_test_patient(client)
    org_id = await create_test_organization(client)
    payload = full_group(p_id, org_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_group(data)
    assert data["type"] == "person"
    assert data["actual"] is True
    assert data["active"] is True
    assert data["name"] == "Diabetes Support Group"
    assert data["quantity"] == 1
    assert data["code"]["text"] == "Community health"
    assert data["managing_entity"] == f"Organization/{org_id}"
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "GRP-001"
    assert len(data["characteristic"]) == 1
    assert data["characteristic"][0]["value_boolean"] is True
    assert len(data["member"]) == 1
    assert data["member"][0]["entity"] == f"Patient/{p_id}"


async def test_create_group_fhir_format(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/", json=minimal_group(), headers=FHIR_ACCEPT
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_group(data)
    assert data["type"] == "person"
    assert data["actual"] is True
    assert int(data["id"]) >= 430000


async def test_create_group_invalid_ref_422(client):
    payload = minimal_group()
    payload["managing_entity"] = "Organization/999999"
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text


# ── Get by ID ────────────────────────────────────────────────────────────


async def test_get_group_plain(client):
    gid = await create_group(client)
    resp = await client.get(f"{BASE}/{gid}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_group(data)
    assert data["id"] == gid


async def test_get_group_fhir(client):
    gid = await create_group(client)
    resp = await client.get(f"{BASE}/{gid}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_group(data)
    assert data["id"] == str(gid)


async def test_get_group_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_group_scalar_and_collections(client):
    p_id1 = await create_test_patient(client)
    p_id2 = await create_test_patient(client)
    gid = await create_group(client, patient_id=p_id1)

    # Patch scalar and replace member list wholesale
    patch_payload = {
        "name": "Updated Group Name",
        "quantity": 2,
        "member": [
            {"entity": f"Patient/{p_id2}", "entity_display": "Second Patient", "inactive": False}
        ],
    }
    resp = await client.patch(f"{BASE}/{gid}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["name"] == "Updated Group Name"
    assert data["quantity"] == 2
    assert len(data["member"]) == 1
    assert data["member"][0]["entity"] == f"Patient/{p_id2}"


async def test_patch_group_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"name": "Ghost Group"})
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_groups_plain(client):
    await create_group(client)
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data, min_total=1)


async def test_list_groups_fhir(client):
    await create_group(client)
    resp = await client.get(f"{BASE}/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data, min_total=1)


async def test_list_groups_filters(client):
    p_id = await create_test_patient(client)
    gid = await create_group(client, patient_id=p_id)

    # Filter by type
    resp = await client.get(f"{BASE}/?type=person")
    assert resp.status_code == 200
    ids = [g["id"] for g in resp.json()["data"]]
    assert gid in ids

    # Filter by name
    resp = await client.get(f"{BASE}/?name=Diabetes")
    assert resp.status_code == 200
    ids = [g["id"] for g in resp.json()["data"]]
    assert gid in ids

    # Filter by member
    resp = await client.get(f"{BASE}/?member=Patient/{p_id}")
    assert resp.status_code == 200
    ids = [g["id"] for g in resp.json()["data"]]
    assert gid in ids


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_group(client):
    gid = await create_group(client)
    resp = await client.delete(f"{BASE}/{gid}")
    assert resp.status_code == 204

    resp = await client.get(f"{BASE}/{gid}")
    assert resp.status_code == 404


# ── Auth & Multi-Tenancy ─────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    # Org A creates Group
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-alpha", permissions=GROUP_PERMS
    )
    resp = await client.post(BASE + "/", json=minimal_group())
    assert resp.status_code == 201
    gid = resp.json()["id"]

    # Org B attempts to read, patch, delete -> all 404
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-beta", permissions=GROUP_PERMS
    )
    assert (await client.get(f"{BASE}/{gid}")).status_code == 404
    assert (await client.patch(f"{BASE}/{gid}", json={"name": "Hacked"})).status_code == 404
    assert (await client.delete(f"{BASE}/{gid}")).status_code == 404


async def test_org_less_token_rejected_403(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None, permissions=GROUP_PERMS
    )
    resp = await client.post(BASE + "/", json=minimal_group())
    assert resp.status_code == 403

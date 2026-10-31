"""Core specimen endpoint coverage.

Specimen has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
Every supplied sub-resource list on create/patch replaces corresponding rows wholesale.

This file holds:
- create (minimal + full nested payload, FHIR format, validation, reference check)
- read (plain + FHIR, not found)
- patch (field updates, sub-list replace, clear, not found)
- list (plain, FHIR bundle, filters, pagination)
- delete
- auth: cross-org isolation and org-less rejection
"""

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import (
    assert_fhir_bundle,
    assert_fhir_specimen,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_specimen,
)
from tests.integration.specimen.support import (
    BASE,
    FHIR_ACCEPT,
    create_specimen,
    create_test_patient,
    full_specimen,
    minimal_specimen,
)

SPECIMEN_PERMS = [
    "specimen:create",
    "specimen:read",
    "specimen:update",
    "specimen:delete",
    "patient:create",
    "patient:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_specimen_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_specimen(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_specimen(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["type"]["text"] == "Venous blood"


async def test_create_specimen_full(client):
    p_id = await create_test_patient(client)
    payload = full_specimen(p_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_specimen(data)
    assert data["status"] == "available"
    assert data["accession_identifier"]["value"] == "ACC-2026-001"
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "SPEC-001"
    assert data["collection"]["quantity_value"] == 10.0
    assert len(data["processing"]) == 1
    assert len(data["container"]) == 1
    assert len(data["condition"]) == 1
    assert len(data["note"]) == 1


async def test_create_specimen_fhir_format(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/", json=minimal_specimen(p_id), headers=FHIR_ACCEPT
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_specimen(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["type"]["text"] == "Venous blood"


async def test_create_specimen_invalid_reference(client):
    payload = minimal_specimen(999999)  # Non-existent patient
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text
    assert_operation_outcome(resp.json(), 422, 422)


async def test_create_specimen_base_r4_validation(client):
    # Invalid FHIR structure - extra/forbidden fields caught by pydantic or base R4
    p_id = await create_test_patient(client)
    payload = minimal_specimen(p_id)
    payload["invalid_field"] = "bad"
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_specimen_plain(client):
    p_id = await create_test_patient(client)
    created = await create_specimen(client, p_id)
    resp = await client.get(f"{BASE}/{created['id']}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_specimen(data, id=created["id"])


async def test_get_specimen_fhir(client):
    p_id = await create_test_patient(client)
    created = await create_specimen(client, p_id)
    resp = await client.get(f"{BASE}/{created['id']}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_specimen(data, id=str(created["id"]))


async def test_get_specimen_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, 404)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_specimen_scalar(client):
    p_id = await create_test_patient(client)
    created = await create_specimen(client, p_id)

    patch_payload = {
        "status": "unavailable",
    }
    resp = await client.patch(f"{BASE}/{created['id']}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "unavailable"


async def test_patch_specimen_replace_sub_lists(client):
    p_id = await create_test_patient(client)
    created = await create_specimen(client, p_id)

    patch_payload = {
        "note": [
            {
                "author_string": "Dr. House",
                "text": "Check electrolyte panel.",
            }
        ]
    }
    resp = await client.patch(f"{BASE}/{created['id']}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["note"]) == 1
    assert data["note"][0]["author_string"] == "Dr. House"


async def test_patch_specimen_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "unavailable"})
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, 404)


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_specimens_plain(client):
    p_id = await create_test_patient(client)
    await create_specimen(client, p_id)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    assert len(data["data"]) >= 1


async def test_list_specimens_fhir_bundle(client):
    p_id = await create_test_patient(client)
    await create_specimen(client, p_id)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)


async def test_list_specimens_filters(client):
    p_id = await create_test_patient(client)
    created = await create_specimen(
        client,
        p_id,
        status="available",
        accession_identifier={
            "value": "ACC-FILTER-1",
        },
    )

    # Filter by subject
    resp = await client.get(f"{BASE}/?subject=Patient/{p_id}")
    assert resp.status_code == 200
    assert any(s["id"] == created["id"] for s in resp.json()["data"])

    # Filter by status
    resp = await client.get(f"{BASE}/?status=available")
    assert resp.status_code == 200
    assert any(s["id"] == created["id"] for s in resp.json()["data"])

    # Filter by accession_identifier
    resp = await client.get(f"{BASE}/?accession_identifier=ACC-FILTER-1")
    assert resp.status_code == 200
    assert any(s["id"] == created["id"] for s in resp.json()["data"])

    # Filter by non-existent accession_identifier
    resp = await client.get(f"{BASE}/?accession_identifier=NONEXISTENT")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 0


async def test_list_specimens_pagination(client):
    p_id = await create_test_patient(client)
    await create_specimen(client, p_id)
    await create_specimen(client, p_id)

    resp = await client.get(f"{BASE}/?limit=1&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 1
    assert len(data["data"]) == 1


# ── Me ───────────────────────────────────────────────────────────────────


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_specimen(client):
    p_id = await create_test_patient(client)
    created = await create_specimen(client, p_id)
    resp = await client.delete(f"{BASE}/{created['id']}")
    assert resp.status_code == 204

    resp = await client.get(f"{BASE}/{created['id']}")
    assert resp.status_code == 404


async def test_delete_specimen_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, 404)


# ── Auth & Tenancy ───────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    # Create specimen in org-1
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-1", permissions=SPECIMEN_PERMS
    )
    p_id = await create_test_patient(client)
    created = await create_specimen(client, p_id)

    # Org-2 cannot get it (returns 404 to avoid leaking existence)
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-2", permissions=SPECIMEN_PERMS
    )
    resp = await client.get(f"{BASE}/{created['id']}")
    assert resp.status_code == 404

    # Org-2 cannot patch it
    resp = await client.patch(f"{BASE}/{created['id']}", json={"status": "unavailable"})
    assert resp.status_code == 404

    # Org-2 cannot delete it
    resp = await client.delete(f"{BASE}/{created['id']}")
    assert resp.status_code == 404


async def test_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None, permissions=SPECIMEN_PERMS
    )
    resp = await client.post(BASE + "/", json={"status": "available"})
    assert resp.status_code == 403

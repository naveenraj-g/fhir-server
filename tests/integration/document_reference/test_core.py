"""Core document_reference endpoint coverage.

DocumentReference has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_document_reference,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_document_reference,
)
from tests.integration.document_reference.support import (
    BASE,
    FHIR_ACCEPT,
    create_document_reference,
    create_test_patient,
    create_test_practitioner,
    full_document_reference,
    minimal_document_reference,
)

DOC_REF_PERMS = [
    "document_reference:create",
    "document_reference:read",
    "document_reference:update",
    "document_reference:delete",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_document_reference_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_document_reference(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_document_reference(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "current"
    assert len(data["content"]) == 1
    assert data["content"][0]["attachment"]["url"] == "https://example.org/docs/1.pdf"


async def test_create_document_reference_full(client):
    p_id = await create_test_patient(client)
    pr_id = await create_test_practitioner(client)
    payload = full_document_reference(p_id, pr_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_document_reference(data)
    assert data["status"] == "current"
    assert data["doc_status"] == "final"
    assert data["type"]["text"] == "Outpatient Note"
    assert len(data["category"]) == 1
    assert len(data["author"]) == 1
    assert data["author"][0]["reference"] == f"Practitioner/{pr_id}"
    assert len(data["security_label"]) == 1
    assert len(data["content"]) == 1
    assert data["content"][0]["attachment"]["size"] == 2048
    assert data["context"]["facility_type"]["text"] == "Hospital"


async def test_create_document_reference_fhir_format(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/", json=minimal_document_reference(p_id), headers=FHIR_ACCEPT
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_document_reference(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "current"
    assert len(data["content"]) == 1
    assert data["content"][0]["attachment"]["url"] == "https://example.org/docs/1.pdf"


async def test_create_document_reference_invalid_reference(client):
    payload = minimal_document_reference(999999)  # Non-existent patient
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text
    assert_operation_outcome(resp.json(), 422, 422)


async def test_create_document_reference_base_r4_validation(client):
    p_id = await create_test_patient(client)
    payload = minimal_document_reference(p_id)
    payload["invalid_field"] = "bad"
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_document_reference_plain(client):
    p_id = await create_test_patient(client)
    created = await create_document_reference(client, p_id)
    resp = await client.get(f"{BASE}/{created['id']}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_document_reference(data, id=created["id"])


async def test_get_document_reference_fhir(client):
    p_id = await create_test_patient(client)
    created = await create_document_reference(client, p_id)
    resp = await client.get(f"{BASE}/{created['id']}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_document_reference(data, id=str(created["id"]))


async def test_get_document_reference_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, 404)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_document_reference_scalar(client):
    p_id = await create_test_patient(client)
    created = await create_document_reference(client, p_id)

    patch_payload = {
        "status": "superseded",
        "description": "Updated summary description",
    }
    resp = await client.patch(f"{BASE}/{created['id']}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "superseded"
    assert data["description"] == "Updated summary description"


async def test_patch_document_reference_replace_sub_lists(client):
    p_id = await create_test_patient(client)
    created = await create_document_reference(client, p_id)

    patch_payload = {
        "content": [
            {
                "attachment": {
                    "url": "https://example.org/docs/v2.pdf",
                    "title": "Version 2 Summary",
                }
            }
        ]
    }
    resp = await client.patch(f"{BASE}/{created['id']}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["content"]) == 1
    assert data["content"][0]["attachment"]["url"] == "https://example.org/docs/v2.pdf"


async def test_patch_document_reference_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "superseded"})
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, 404)


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_document_references_plain(client):
    p_id = await create_test_patient(client)
    await create_document_reference(client, p_id)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    assert len(data["data"]) >= 1


async def test_list_document_references_fhir_bundle(client):
    p_id = await create_test_patient(client)
    await create_document_reference(client, p_id)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)


async def test_list_document_references_filters(client):
    p_id = await create_test_patient(client)
    created = await create_document_reference(
        client,
        p_id,
        status="current",
        doc_status="final",
        description="Filterable consultation note",
    )

    # Filter by subject
    resp = await client.get(f"{BASE}/?subject=Patient/{p_id}")
    assert resp.status_code == 200
    assert any(d["id"] == created["id"] for d in resp.json()["data"])

    # Filter by status
    resp = await client.get(f"{BASE}/?status=current")
    assert resp.status_code == 200
    assert any(d["id"] == created["id"] for d in resp.json()["data"])

    # Filter by doc_status
    resp = await client.get(f"{BASE}/?doc_status=final")
    assert resp.status_code == 200
    assert any(d["id"] == created["id"] for d in resp.json()["data"])

    # Filter by description
    resp = await client.get(f"{BASE}/?description=Filterable")
    assert resp.status_code == 200
    assert any(d["id"] == created["id"] for d in resp.json()["data"])

    # Filter by non-existent description
    resp = await client.get(f"{BASE}/?description=NONEXISTENT_XYZ")
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 0


async def test_list_document_references_pagination(client):
    p_id = await create_test_patient(client)
    await create_document_reference(client, p_id)
    await create_document_reference(client, p_id)

    resp = await client.get(f"{BASE}/?limit=1&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 1
    assert len(data["data"]) == 1


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_document_reference(client):
    p_id = await create_test_patient(client)
    created = await create_document_reference(client, p_id)
    resp = await client.delete(f"{BASE}/{created['id']}")
    assert resp.status_code == 204

    resp = await client.get(f"{BASE}/{created['id']}")
    assert resp.status_code == 404


async def test_delete_document_reference_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, 404)


# ── Auth & Tenancy ───────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    # Create document_reference in org-1
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-1", permissions=DOC_REF_PERMS
    )
    p_id = await create_test_patient(client)
    created = await create_document_reference(client, p_id)

    # Org-2 cannot get it (returns 404 to avoid leaking existence)
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-2", permissions=DOC_REF_PERMS
    )
    resp = await client.get(f"{BASE}/{created['id']}")
    assert resp.status_code == 404

    # Org-2 cannot patch it
    resp = await client.patch(f"{BASE}/{created['id']}", json={"status": "superseded"})
    assert resp.status_code == 404

    # Org-2 cannot delete it
    resp = await client.delete(f"{BASE}/{created['id']}")
    assert resp.status_code == 404


async def test_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None, permissions=DOC_REF_PERMS
    )
    resp = await client.post(
        BASE + "/",
        json={
            "status": "current",
            "subject": "Patient/10001",
            "content": [{"attachment": {"url": "https://example.org/1.pdf"}}],
        },
    )
    assert resp.status_code == 403

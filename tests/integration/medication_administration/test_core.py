"""Core MedicationAdministration endpoint coverage.

MedicationAdministration has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_medication_administration,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_medication_administration,
)
from tests.integration.medication_administration.support import (
    BASE,
    FHIR_ACCEPT,
    create_medication_administration,
    create_test_condition,
    create_test_patient,
    create_test_practitioner,
    full_medication_administration,
    minimal_medication_administration,
)

MEDICATION_ADMINISTRATION_PERMS = [
    "medication_administration:create",
    "medication_administration:read",
    "medication_administration:update",
    "medication_administration:delete",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "condition:create",
    "condition:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_medication_administration_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_medication_administration(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_medication_administration(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "completed"
    assert data["medication_codeable_concept"]["text"] == "Amoxicillin 500mg capsule"
    assert data["effective_date_time"].startswith("2026-01-15T10:00:00")


async def test_create_medication_administration_full(client):
    p_id = await create_test_patient(client)
    pr_id = await create_test_practitioner(client)
    c_id = await create_test_condition(client, p_id)
    payload = full_medication_administration(p_id, pr_id, c_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_medication_administration(data)
    assert data["status"] == "completed"
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["category"]["text"] == "Inpatient"
    assert len(data["reason_code"]) == 1
    assert data["reason_code"][0]["text"] == "Bacterial infection"
    assert len(data["reason_reference"]) == 1
    assert data["reason_reference"][0]["reference"] == f"Condition/{c_id}"
    assert len(data["performer"]) == 1
    assert data["performer"][0]["actor"]["reference"] == f"Practitioner/{pr_id}"
    assert len(data["note"]) == 1
    assert data["dosage"]["route"]["text"] == "Oral"
    assert data["dosage"]["dose"]["value"] == 500.0


async def test_create_medication_administration_fhir_format(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/",
        json=minimal_medication_administration(p_id),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_medication_administration(data)
    assert data["resourceType"] == "MedicationAdministration"
    assert data["status"] == "completed"
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["medicationCodeableConcept"]["text"] == "Amoxicillin 500mg capsule"


async def test_create_medication_administration_invalid_status_422(client):
    p_id = await create_test_patient(client)
    payload = minimal_medication_administration(p_id)
    payload["status"] = "invalid-status-value"
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text


async def test_create_medication_administration_nonexistent_reference_422(client):
    payload = minimal_medication_administration(99999999)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text
    assert_operation_outcome(resp.json(), 422, resp.status_code)


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_medication_administration_plain(client):
    p_id = await create_test_patient(client)
    created = await create_medication_administration(
        client, minimal_medication_administration(p_id)
    )
    ma_id = created["id"]

    resp = await client.get(f"{BASE}/{ma_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_medication_administration(data)
    assert data["id"] == ma_id
    assert data["subject"]["reference"] == f"Patient/{p_id}"


async def test_get_medication_administration_fhir(client):
    p_id = await create_test_patient(client)
    created = await create_medication_administration(
        client, minimal_medication_administration(p_id)
    )
    ma_id = created["id"]

    resp = await client.get(f"{BASE}/{ma_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_medication_administration(data)
    assert data["resourceType"] == "MedicationAdministration"
    assert data["id"] == str(ma_id)
    assert data["subject"]["reference"] == f"Patient/{p_id}"


async def test_get_medication_administration_not_found(client):
    resp = await client.get(f"{BASE}/99999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_medication_administration_fields(client):
    p_id = await create_test_patient(client)
    created = await create_medication_administration(
        client, minimal_medication_administration(p_id)
    )
    ma_id = created["id"]

    patch_payload = {
        "status": "stopped",
    }
    resp = await client.patch(f"{BASE}/{ma_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_medication_administration(data)
    assert data["status"] == "stopped"
    assert data["subject"]["reference"] == f"Patient/{p_id}"


async def test_patch_medication_administration_sublists_replaced(client):
    p_id = await create_test_patient(client)
    created = await create_medication_administration(
        client, full_medication_administration(p_id)
    )
    ma_id = created["id"]
    assert len(created["note"]) == 1

    # Replace notes with two new ones
    patch_payload = {
        "note": [
            {"text": "Updated note 1", "time": "2026-02-01T12:00:00Z"},
            {"text": "Updated note 2", "time": "2026-02-02T12:00:00Z"},
        ]
    }
    resp = await client.patch(f"{BASE}/{ma_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["note"]) == 2
    note_texts = [n["text"] for n in data["note"]]
    assert "Updated note 1" in note_texts
    assert "Updated note 2" in note_texts


async def test_patch_medication_administration_not_found(client):
    resp = await client.patch(f"{BASE}/99999999", json={"status": "stopped"})
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_medication_administrations_plain(client):
    p_id = await create_test_patient(client)
    await create_medication_administration(client, minimal_medication_administration(p_id))

    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    assert len(data["data"]) >= 1
    assert_plain_medication_administration(data["data"][0])


async def test_list_medication_administrations_fhir_bundle(client):
    p_id = await create_test_patient(client)
    await create_medication_administration(client, minimal_medication_administration(p_id))

    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    assert len(data["entry"]) >= 1
    assert_fhir_medication_administration(data["entry"][0]["resource"])


async def test_list_medication_administrations_filters(client):
    p_id = await create_test_patient(client)
    payload = minimal_medication_administration(p_id)
    payload["medication_codeable_concept"]["text"] = "UniqueMedAdminXYZ"
    payload["category"] = {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/med-admin-category",
                "code": "community",
                "display": "Community",
            }
        ],
        "text": "Community",
    }
    created = await create_medication_administration(client, payload)
    ma_id = created["id"]

    # Filter by status
    resp = await client.get(f"{BASE}/?status=completed")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert ma_id in ids

    # Filter by patient
    resp = await client.get(f"{BASE}/?patient=Patient/{p_id}")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert ma_id in ids

    # Filter by code
    resp = await client.get(f"{BASE}/?code=UniqueMedAdminXYZ")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert ma_id in ids

    # Filter by category
    resp = await client.get(f"{BASE}/?category=community")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert ma_id in ids


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_medication_administration(client):
    p_id = await create_test_patient(client)
    created = await create_medication_administration(
        client, minimal_medication_administration(p_id)
    )
    ma_id = created["id"]

    del_resp = await client.delete(f"{BASE}/{ma_id}")
    assert del_resp.status_code == 204, del_resp.text

    get_resp = await client.get(f"{BASE}/{ma_id}")
    assert get_resp.status_code == 404


# ── Multi-Tenancy & Auth ──────────────────────────────────────────────────


async def test_medication_administration_cross_org_isolation(client):
    """Resource created under org-1 returns 404 (not 403) to a caller in org-2."""
    p_id = await create_test_patient(client)
    created = await create_medication_administration(
        client, minimal_medication_administration(p_id)
    )
    ma_id = created["id"]

    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="different-org-id",
        permissions=MEDICATION_ADMINISTRATION_PERMS,
    )
    try:
        resp = await client.get(f"{BASE}/{ma_id}")
        assert resp.status_code == 404, resp.text
        assert_operation_outcome(resp.json(), 404, resp.status_code)

        patch_resp = await client.patch(
            f"{BASE}/{ma_id}", json={"status": "stopped"}
        )
        assert patch_resp.status_code == 404

        del_resp = await client.delete(f"{BASE}/{ma_id}")
        assert del_resp.status_code == 404
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=MEDICATION_ADMINISTRATION_PERMS
        )


async def test_medication_administration_org_less_token_rejected(client):
    """An org-less token is rejected with 403 on create and list."""
    p_id = await create_test_patient(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=MEDICATION_ADMINISTRATION_PERMS,
    )
    try:
        resp = await client.post(
            BASE + "/",
            json=minimal_medication_administration(p_id),
        )
        assert resp.status_code == 403, resp.text

        list_resp = await client.get(BASE + "/")
        assert list_resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=MEDICATION_ADMINISTRATION_PERMS
        )

"""Core MedicationDispense endpoint coverage.

MedicationDispense has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_medication_dispense,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_medication_dispense,
)
from tests.integration.medication_dispense.support import (
    BASE,
    FHIR_ACCEPT,
    create_medication_dispense,
    create_test_location,
    create_test_patient,
    create_test_practitioner,
    full_medication_dispense,
    minimal_medication_dispense,
)

MEDICATION_DISPENSE_PERMS = [
    "medication_dispense:create",
    "medication_dispense:read",
    "medication_dispense:update",
    "medication_dispense:delete",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "location:create",
    "location:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_medication_dispense_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_medication_dispense(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_medication_dispense(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "completed"
    assert data["medication_codeable_concept"]["text"] == "Amoxicillin 500 MG Oral Tablet"
    assert data["quantity"]["value"] == 30.0
    assert data["days_supply"]["value"] == 10.0


async def test_create_medication_dispense_full(client):
    p_id = await create_test_patient(client)
    pr_id = await create_test_practitioner(client)
    loc_id = await create_test_location(client)
    payload = full_medication_dispense(p_id, pr_id, loc_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_medication_dispense(data)
    assert data["status"] == "completed"
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["category"]["text"] == "Inpatient"
    assert data["type"]["text"] == "First Fill"
    assert data["quantity"]["value"] == 30.0
    assert data["days_supply"]["value"] == 10.0
    assert len(data["performer"]) == 1
    assert data["performer"][0]["actor"]["reference"] == f"Practitioner/{pr_id}"
    assert data["location"]["reference"] == f"Location/{loc_id}"
    assert data["destination"]["reference"] == f"Location/{loc_id}"
    assert len(data["receiver"]) == 1
    assert data["receiver"][0]["reference"] == f"Patient/{p_id}"
    assert len(data["note"]) == 1
    assert data["note"][0]["text"] == "Patient advised to take with food."
    assert len(data["dosage_instruction"]) == 1
    assert data["dosage_instruction"][0]["text"] == "Take 1 tablet by mouth 3 times daily with meals"
    assert data["substitution"] is not None
    assert data["substitution"]["was_substituted"] is True
    assert data["substitution"]["type"]["text"] == "Generic"


async def test_create_medication_dispense_fhir_format(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/",
        json=minimal_medication_dispense(p_id),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_medication_dispense(data)
    assert data["resourceType"] == "MedicationDispense"
    assert data["status"] == "completed"
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["medicationCodeableConcept"]["text"] == "Amoxicillin 500 MG Oral Tablet"


async def test_create_medication_dispense_invalid_status_422(client):
    p_id = await create_test_patient(client)
    payload = minimal_medication_dispense(p_id)
    payload["status"] = "invalid-status-value"
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text


async def test_create_medication_dispense_nonexistent_reference_422(client):
    payload = minimal_medication_dispense(99999999)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text
    assert_operation_outcome(resp.json(), 422, resp.status_code)


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_medication_dispense_plain(client):
    p_id = await create_test_patient(client)
    created = await create_medication_dispense(
        client, minimal_medication_dispense(p_id)
    )
    md_id = created["id"]

    resp = await client.get(f"{BASE}/{md_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_medication_dispense(data)
    assert data["id"] == md_id
    assert data["subject"]["reference"] == f"Patient/{p_id}"


async def test_get_medication_dispense_fhir(client):
    p_id = await create_test_patient(client)
    created = await create_medication_dispense(
        client, minimal_medication_dispense(p_id)
    )
    md_id = created["id"]

    resp = await client.get(f"{BASE}/{md_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_medication_dispense(data)
    assert data["resourceType"] == "MedicationDispense"
    assert data["id"] == str(md_id)
    assert data["subject"]["reference"] == f"Patient/{p_id}"


async def test_get_medication_dispense_not_found(client):
    resp = await client.get(f"{BASE}/99999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_medication_dispense_fields(client):
    p_id = await create_test_patient(client)
    created = await create_medication_dispense(
        client, minimal_medication_dispense(p_id)
    )
    md_id = created["id"]

    patch_payload = {
        "status": "stopped",
    }
    resp = await client.patch(f"{BASE}/{md_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_medication_dispense(data)
    assert data["status"] == "stopped"
    assert data["subject"]["reference"] == f"Patient/{p_id}"


async def test_patch_medication_dispense_sublists_replaced(client):
    p_id = await create_test_patient(client)
    created = await create_medication_dispense(
        client, full_medication_dispense(p_id)
    )
    md_id = created["id"]
    assert len(created["note"]) == 1

    # Replace notes with two new ones
    patch_payload = {
        "note": [
            {"text": "Updated dispense note 1", "time": "2026-02-01T12:00:00Z"},
            {"text": "Updated dispense note 2", "time": "2026-02-02T12:00:00Z"},
        ]
    }
    resp = await client.patch(f"{BASE}/{md_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["note"]) == 2
    note_texts = [n["text"] for n in data["note"]]
    assert "Updated dispense note 1" in note_texts
    assert "Updated dispense note 2" in note_texts


async def test_patch_medication_dispense_not_found(client):
    resp = await client.patch(f"{BASE}/99999999", json={"status": "stopped"})
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_medication_dispenses_plain(client):
    p_id = await create_test_patient(client)
    await create_medication_dispense(client, minimal_medication_dispense(p_id))

    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    assert len(data["data"]) >= 1
    assert_plain_medication_dispense(data["data"][0])


async def test_list_medication_dispenses_fhir_bundle(client):
    p_id = await create_test_patient(client)
    await create_medication_dispense(client, minimal_medication_dispense(p_id))

    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    assert len(data["entry"]) >= 1
    assert_fhir_medication_dispense(data["entry"][0]["resource"])


async def test_list_medication_dispenses_filters(client):
    p_id = await create_test_patient(client)
    payload = minimal_medication_dispense(p_id)
    payload["medication_codeable_concept"]["text"] = "UniqueMedDispenseXYZ"
    payload["category"] = {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/medicationdispense-category",
                "code": "community",
                "display": "Community",
            }
        ],
        "text": "Community",
    }
    payload["type"] = {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActPharmacySupplyType",
                "code": "RF",
                "display": "Refill",
            }
        ],
        "text": "Refill",
    }
    created = await create_medication_dispense(client, payload)
    md_id = created["id"]

    # Filter by status
    resp = await client.get(f"{BASE}/?status=completed")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert md_id in ids

    # Filter by patient
    resp = await client.get(f"{BASE}/?patient=Patient/{p_id}")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert md_id in ids

    # Filter by code
    resp = await client.get(f"{BASE}/?code=UniqueMedDispenseXYZ")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert md_id in ids

    # Filter by category
    resp = await client.get(f"{BASE}/?category=community")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert md_id in ids

    # Filter by type
    resp = await client.get(f"{BASE}/?type=RF")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert md_id in ids


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_medication_dispense(client):
    p_id = await create_test_patient(client)
    created = await create_medication_dispense(
        client, minimal_medication_dispense(p_id)
    )
    md_id = created["id"]

    del_resp = await client.delete(f"{BASE}/{md_id}")
    assert del_resp.status_code == 204, del_resp.text

    get_resp = await client.get(f"{BASE}/{md_id}")
    assert get_resp.status_code == 404


# ── Multi-Tenancy & Auth ──────────────────────────────────────────────────


async def test_medication_dispense_cross_org_isolation(client):
    """Resource created under org-1 returns 404 (not 403) to a caller in org-2."""
    p_id = await create_test_patient(client)
    created = await create_medication_dispense(
        client, minimal_medication_dispense(p_id)
    )
    md_id = created["id"]

    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="different-org-id",
        permissions=MEDICATION_DISPENSE_PERMS,
    )
    try:
        resp = await client.get(f"{BASE}/{md_id}")
        assert resp.status_code == 404, resp.text
        assert_operation_outcome(resp.json(), 404, resp.status_code)

        patch_resp = await client.patch(
            f"{BASE}/{md_id}", json={"status": "stopped"}
        )
        assert patch_resp.status_code == 404

        del_resp = await client.delete(f"{BASE}/{md_id}")
        assert del_resp.status_code == 404
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=MEDICATION_DISPENSE_PERMS
        )


async def test_medication_dispense_org_less_token_rejected(client):
    """An org-less token is rejected with 403 on create and list."""
    p_id = await create_test_patient(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=MEDICATION_DISPENSE_PERMS,
    )
    try:
        resp = await client.post(
            BASE + "/",
            json=minimal_medication_dispense(p_id),
        )
        assert resp.status_code == 403, resp.text

        list_resp = await client.get(BASE + "/")
        assert list_resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=MEDICATION_DISPENSE_PERMS
        )

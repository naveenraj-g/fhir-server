"""Core Immunization endpoint coverage.

Immunization has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_immunization,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_immunization,
)
from tests.integration.immunization.support import (
    BASE,
    FHIR_ACCEPT,
    create_immunization,
    create_test_condition,
    create_test_location,
    create_test_organization,
    create_test_patient,
    create_test_practitioner,
    full_immunization,
    minimal_immunization,
)

IMMUNIZATION_PERMS = [
    "immunization:create",
    "immunization:read",
    "immunization:update",
    "immunization:delete",
    "patient:create",
    "patient:read",
    "condition:create",
    "condition:read",
    "practitioner:create",
    "practitioner:read",
    "location:create",
    "location:read",
    "organization:create",
    "organization:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_immunization_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_immunization(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_immunization(data)
    assert data["patient"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "completed"
    assert data["primary_source"] is True
    assert data["vaccine_code"]["text"] == "COVID-19 mRNA"


async def test_create_immunization_full(client):
    p_id = await create_test_patient(client)
    c_id = await create_test_condition(client, p_id)
    pr_id = await create_test_practitioner(client)
    loc_id = await create_test_location(client)
    org_id = await create_test_organization(client)

    payload = full_immunization(
        p_id,
        condition_id=c_id,
        practitioner_id=pr_id,
        location_id=loc_id,
        org_id=org_id,
    )
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_immunization(data)
    assert data["status"] == "completed"
    assert data["patient"]["reference"] == f"Patient/{p_id}"
    assert data["status_reason"]["text"] == "Medical precaution cleared"
    assert data["location"]["reference"] == f"Location/{loc_id}"
    assert data["manufacturer"]["reference"] == f"Organization/{org_id}"
    assert len(data["performer"]) == 1
    assert data["performer"][0]["actor"]["reference"] == f"Practitioner/{pr_id}"
    assert len(data["reason_code"]) == 1
    assert len(data["reason_reference"]) == 1
    assert data["reason_reference"][0]["reference"] == f"Condition/{c_id}"
    assert len(data["education"]) == 1
    assert len(data["protocol_applied"]) == 1
    assert data["protocol_applied"][0]["series"] == "COVID-19 Primary Series"


async def test_create_immunization_fhir_format(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/",
        json=minimal_immunization(p_id),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_immunization(data)
    assert data["resourceType"] == "Immunization"
    assert data["status"] == "completed"
    assert data["patient"]["reference"] == f"Patient/{p_id}"
    assert data["vaccineCode"]["text"] == "COVID-19 mRNA"


async def test_create_immunization_invalid_status_422(client):
    p_id = await create_test_patient(client)
    payload = minimal_immunization(p_id)
    payload["status"] = "invalid-status-value"
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text


async def test_create_immunization_nonexistent_patient_422(client):
    payload = minimal_immunization(999999)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text
    assert_operation_outcome(resp.json(), 422, resp.status_code)


# ── Read ──────────────────────────────────────────────────────────────────


async def test_get_immunization_plain(client):
    p_id = await create_test_patient(client)
    imm_id = await create_immunization(client, minimal_immunization(p_id))

    resp = await client.get(f"{BASE}/{imm_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_immunization(data, id=imm_id, status="completed")
    assert data["patient"]["reference"] == f"Patient/{p_id}"


async def test_get_immunization_fhir(client):
    p_id = await create_test_patient(client)
    imm_id = await create_immunization(client, minimal_immunization(p_id))

    resp = await client.get(f"{BASE}/{imm_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_immunization(data, id=str(imm_id), status="completed")
    assert data["resourceType"] == "Immunization"


async def test_get_immunization_not_found_404(client):
    resp = await client.get(f"{BASE}/99999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ─────────────────────────────────────────────────────────────────


async def test_patch_immunization_fields(client):
    p_id = await create_test_patient(client)
    imm_id = await create_immunization(client, minimal_immunization(p_id))

    resp = await client.patch(
        f"{BASE}/{imm_id}",
        json={"lot_number": "LOT-PATCHED", "is_subpotent": True},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_immunization(data, id=imm_id)
    assert data["lot_number"] == "LOT-PATCHED"
    assert data["is_subpotent"] is True
    # unpatched fields preserved
    assert data["status"] == "completed"
    assert data["patient"]["reference"] == f"Patient/{p_id}"


async def test_patch_immunization_replace_sub_lists(client):
    p_id = await create_test_patient(client)
    imm_id = await create_immunization(client, minimal_immunization(p_id))

    # Add a note
    resp = await client.patch(
        f"{BASE}/{imm_id}",
        json={
            "note": [
                {
                    "text": "Initial post-vaccination check normal.",
                    "time": "2026-01-15T10:10:00Z",
                }
            ]
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["note"]) == 1
    assert data["note"][0]["text"] == "Initial post-vaccination check normal."

    # Replace note list
    resp = await client.patch(
        f"{BASE}/{imm_id}",
        json={
            "note": [
                {
                    "text": "Updated note: mild soreness reported.",
                    "time": "2026-01-15T12:00:00Z",
                }
            ]
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["note"]) == 1
    assert data["note"][0]["text"] == "Updated note: mild soreness reported."


async def test_patch_immunization_not_found_404(client):
    resp = await client.patch(
        f"{BASE}/99999999",
        json={"lot_number": "NONEXISTENT"},
    )
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── List ──────────────────────────────────────────────────────────────────


async def test_list_immunizations_plain(client):
    p_id = await create_test_patient(client)
    imm_id = await create_immunization(client, minimal_immunization(p_id))

    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    ids = [item["id"] for item in data["data"]]
    assert imm_id in ids


async def test_list_immunizations_fhir_bundle(client):
    p_id = await create_test_patient(client)
    imm_id = await create_immunization(client, minimal_immunization(p_id))

    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    entry_ids = [e["resource"]["id"] for e in data.get("entry", [])]
    assert str(imm_id) in entry_ids


async def test_list_immunizations_filter_by_status(client):
    p_id = await create_test_patient(client)
    imm_id = await create_immunization(client, minimal_immunization(p_id))

    resp = await client.get(f"{BASE}/?status=completed")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert imm_id in ids

    resp = await client.get(f"{BASE}/?status=not-done")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert imm_id not in ids


async def test_list_immunizations_filter_by_patient(client):
    p1 = await create_test_patient(client)
    p2 = await create_test_patient(client)
    imm1 = await create_immunization(client, minimal_immunization(p1))
    imm2 = await create_immunization(client, minimal_immunization(p2))

    resp = await client.get(f"{BASE}/?patient=Patient/{p1}")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert imm1 in ids
    assert imm2 not in ids


async def test_list_immunizations_filter_by_date(client):
    p_id = await create_test_patient(client)
    imm_id = await create_immunization(client, minimal_immunization(p_id))

    resp = await client.get(f"{BASE}/?date=2026-01-15")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert imm_id in ids

    resp = await client.get(f"{BASE}/?date=2020-01-01")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert imm_id not in ids


# ── Delete ────────────────────────────────────────────────────────────────


async def test_delete_immunization(client):
    p_id = await create_test_patient(client)
    imm_id = await create_immunization(client, minimal_immunization(p_id))

    resp = await client.delete(f"{BASE}/{imm_id}")
    assert resp.status_code == 204, resp.text

    # Verify deleted
    resp = await client.get(f"{BASE}/{imm_id}")
    assert resp.status_code == 404, resp.text


async def test_delete_immunization_not_found_404(client):
    resp = await client.delete(f"{BASE}/99999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Multi-Tenancy & Auth ──────────────────────────────────────────────────


async def test_immunization_cross_org_isolation_404(client):
    p_id = await create_test_patient(client)
    imm_id = await create_immunization(client, minimal_immunization(p_id))

    # Switch to different org
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="other-org",
        permissions=IMMUNIZATION_PERMS,
    )

    # Cross-org get returns 404, not 403 (never leaks existence)
    resp = await client.get(f"{BASE}/{imm_id}")
    assert resp.status_code == 404, resp.text

    # Cross-org patch returns 404
    resp = await client.patch(f"{BASE}/{imm_id}", json={"lot_number": "ATTACK"})
    assert resp.status_code == 404, resp.text

    # Cross-org delete returns 404
    resp = await client.delete(f"{BASE}/{imm_id}")
    assert resp.status_code == 404, resp.text

    # Cross-org list does not contain resource from other org
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert imm_id not in ids


async def test_immunization_org_less_token_rejected_403(client):
    # Set org-less user
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=IMMUNIZATION_PERMS,
    )

    resp = await client.post(BASE + "/", json=minimal_immunization(10001))
    assert resp.status_code == 403, resp.text
    assert_operation_outcome(resp.json(), 403, resp.status_code)

    resp = await client.get(BASE + "/")
    assert resp.status_code == 403, resp.text
    assert_operation_outcome(resp.json(), 403, resp.status_code)

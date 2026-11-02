"""Core FamilyMemberHistory endpoint coverage.

FamilyMemberHistory has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_family_member_history,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_family_member_history,
)
from tests.integration.family_member_history.support import (
    BASE,
    FHIR_ACCEPT,
    create_family_member_history,
    create_test_condition,
    create_test_patient,
    full_family_member_history,
    minimal_family_member_history,
)

FAMILY_MEMBER_HISTORY_PERMS = [
    "family_member_history:create",
    "family_member_history:read",
    "family_member_history:update",
    "family_member_history:delete",
    "patient:create",
    "patient:read",
    "condition:create",
    "condition:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_family_member_history_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_family_member_history(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_family_member_history(data)
    assert data["patient"] == f"Patient/{p_id}"
    assert data["status"] == "completed"
    assert data["relationship"]["text"] == "Father"


async def test_create_family_member_history_full(client):
    p_id = await create_test_patient(client)
    c_id = await create_test_condition(client, p_id)
    payload = full_family_member_history(p_id, c_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_family_member_history(data)
    assert data["status"] == "completed"
    assert data["patient"] == f"Patient/{p_id}"
    assert data["patient_display"] == "Jane Doe"
    assert data["name"] == "John Doe"
    assert data["sex"]["text"] == "Male"
    assert data["born_date"] == "1950-05-12"
    assert data["age_age_value"] == 75.0
    assert data["estimated_age"] is False
    assert data["deceased_boolean"] is False
    assert len(data["reason_code"]) == 1
    assert data["reason_code"][0]["text"] == "Family history of Type 2 Diabetes"
    assert len(data["reason_reference"]) == 1
    assert data["reason_reference"][0]["reference"] == f"Condition/{c_id}"
    assert len(data["note"]) == 1
    assert "Father was diagnosed with diabetes" in data["note"][0]["text"]
    assert len(data["condition"]) == 1
    assert data["condition"][0]["code"]["text"] == "Type 2 Diabetes"
    assert data["condition"][0]["outcome"]["text"] == "Alive and well managed"
    assert data["condition"][0]["contributed_to_death"] is False
    assert data["condition"][0]["onset_age_value"] == 52.0
    assert len(data["condition"][0]["note"]) == 1


async def test_create_family_member_history_fhir_content_negotiation(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/",
        json=minimal_family_member_history(p_id),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_family_member_history(data)
    assert data["patient"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "completed"
    assert data["relationship"]["text"] == "Father"


async def test_create_family_member_history_reference_validation_nonexistent_patient(
    client,
):
    resp = await client.post(
        BASE + "/",
        json={
            "status": "completed",
            "patient": "Patient/9999999",
            "relationship": {"text": "Father"},
        },
    )
    assert resp.status_code == 422, resp.text


async def test_create_family_member_history_with_reference_identifier_fallback(client):
    """FamilyMemberHistory created with Reference.identifier fallback columns end-to-end."""
    p_id = await create_test_patient(client)
    payload = {
        "status": "completed",
        "patient": f"Patient/{p_id}",
        "patient_display": "Fallback Jane Doe",
        "patient_identifier_system": "http://hospital.example.org/patients",
        "patient_identifier_value": "MRN-FMH-999",
        "relationship": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                    "code": "MTH",
                    "display": "mother",
                }
            ],
            "text": "Mother",
        },
        "identifier": [
            {
                "system": "http://hospital.example.org/family-histories",
                "value": "FMH-001",
            }
        ],
        "reason_reference": [
            {
                "identifier_system": "http://hospital.example.org/conditions",
                "identifier_value": "COND-FALLBACK-1",
                "display": "Condition Fallback",
            }
        ],
    }
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_family_member_history(data)
    assert data["patient_display"] == "Fallback Jane Doe"
    assert data["patient_identifier_system"] == "http://hospital.example.org/patients"
    assert data["patient_identifier_value"] == "MRN-FMH-999"
    assert len(data["reason_reference"]) == 1
    assert (
        data["reason_reference"][0]["identifier_value"] == "COND-FALLBACK-1"
    )

    # FHIR serialization
    fhir_resp = await client.get(f"{BASE}/{data['id']}", headers=FHIR_ACCEPT)
    assert fhir_resp.status_code == 200, fhir_resp.text
    fhir_data = fhir_resp.json()
    assert_fhir_family_member_history(fhir_data)
    assert fhir_data["patient"]["display"] == "Fallback Jane Doe"
    assert (
        fhir_data["patient"]["identifier"]["value"] == "MRN-FMH-999"
    )
    assert (
        fhir_data["reasonReference"][0]["identifier"]["value"]
        == "COND-FALLBACK-1"
    )


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_family_member_history_plain(client):
    p_id = await create_test_patient(client)
    created = await create_family_member_history(
        client, minimal_family_member_history(p_id)
    )
    fmh_id = created["id"]

    resp = await client.get(f"{BASE}/{fmh_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_family_member_history(data)
    assert data["id"] == fmh_id
    assert data["patient"] == f"Patient/{p_id}"


async def test_get_family_member_history_fhir(client):
    p_id = await create_test_patient(client)
    created = await create_family_member_history(
        client, minimal_family_member_history(p_id)
    )
    fmh_id = created["id"]

    resp = await client.get(f"{BASE}/{fmh_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_family_member_history(data)
    assert data["id"] == str(fmh_id)
    assert data["patient"]["reference"] == f"Patient/{p_id}"


async def test_get_family_member_history_not_found(client):
    resp = await client.get(f"{BASE}/9999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_family_member_history_scalar_and_collections(client):
    p_id = await create_test_patient(client)
    created = await create_family_member_history(
        client, minimal_family_member_history(p_id)
    )
    fmh_id = created["id"]

    patch_payload = {
        "name": "Jonathan Doe",
        "estimated_age": True,
        "note": [
            {"text": "Patient mentioned father has a history of high cholesterol."}
        ],
        "condition": [
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "13644009",
                            "display": "Hypercholesterolemia",
                        }
                    ],
                    "text": "Hypercholesterolemia",
                },
                "onset_age_value": 45.0,
            }
        ],
    }

    resp = await client.patch(f"{BASE}/{fmh_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_family_member_history(data)
    assert data["name"] == "Jonathan Doe"
    assert data["estimated_age"] is True
    assert len(data["note"]) == 1
    assert "high cholesterol" in data["note"][0]["text"]
    assert len(data["condition"]) == 1
    assert data["condition"][0]["code"]["text"] == "Hypercholesterolemia"

    # Replace collection
    resp2 = await client.patch(
        f"{BASE}/{fmh_id}",
        json={
            "note": [
                {"text": "Updated note: father also had hypertension."}
            ]
        },
    )
    assert resp2.status_code == 200, resp2.text
    data2 = resp2.json()
    assert len(data2["note"]) == 1
    assert data2["note"][0]["text"] == "Updated note: father also had hypertension."


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_family_member_histories_plain(client):
    p_id = await create_test_patient(client)
    await create_family_member_history(
        client, minimal_family_member_history(p_id)
    )

    resp = await client.get(f"{BASE}/?limit=10")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data, min_total=1)
    assert_plain_family_member_history(data["data"][0])


async def test_list_family_member_histories_fhir_bundle(client):
    p_id = await create_test_patient(client)
    await create_family_member_history(
        client, minimal_family_member_history(p_id)
    )

    resp = await client.get(f"{BASE}/?limit=10", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data, min_total=1)
    assert_fhir_family_member_history(data["entry"][0]["resource"])


async def test_list_family_member_histories_filters(client):
    p_id = await create_test_patient(client)
    created = await create_family_member_history(
        client,
        {
            "status": "partial",
            "patient": f"Patient/{p_id}",
            "relationship": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                        "code": "MTH",
                        "display": "mother",
                    }
                ],
                "text": "Mother",
            },
            "condition": [
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "FMH-FILTER-COND-99",
                                "display": "Special Condition",
                            }
                        ],
                        "text": "Special Condition",
                    }
                }
            ],
        },
    )
    fmh_id = created["id"]

    # Filter by status
    resp = await client.get(f"{BASE}/?status=partial")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert fmh_id in ids

    # Filter by patient
    resp = await client.get(f"{BASE}/?patient=Patient/{p_id}")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert fmh_id in ids

    # Filter by relationship
    resp = await client.get(f"{BASE}/?relationship=MTH")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert fmh_id in ids

    # Filter by code
    resp = await client.get(f"{BASE}/?code=FMH-FILTER-COND-99")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert fmh_id in ids


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_family_member_history(client):
    p_id = await create_test_patient(client)
    created = await create_family_member_history(
        client, minimal_family_member_history(p_id)
    )
    fmh_id = created["id"]

    del_resp = await client.delete(f"{BASE}/{fmh_id}")
    assert del_resp.status_code == 204, del_resp.text

    get_resp = await client.get(f"{BASE}/{fmh_id}")
    assert get_resp.status_code == 404


# ── Multi-Tenancy & Auth ──────────────────────────────────────────────────


async def test_family_member_history_cross_org_isolation(client):
    """Resource created under org-1 returns 404 (not 403) to a caller in org-2."""
    p_id = await create_test_patient(client)
    created = await create_family_member_history(
        client, minimal_family_member_history(p_id)
    )
    fmh_id = created["id"]

    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="different-org-id",
        permissions=FAMILY_MEMBER_HISTORY_PERMS,
    )
    try:
        resp = await client.get(f"{BASE}/{fmh_id}")
        assert resp.status_code == 404, resp.text
        assert_operation_outcome(resp.json(), 404, resp.status_code)

        patch_resp = await client.patch(
            f"{BASE}/{fmh_id}", json={"name": "Attacker"}
        )
        assert patch_resp.status_code == 404

        del_resp = await client.delete(f"{BASE}/{fmh_id}")
        assert del_resp.status_code == 404
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=FAMILY_MEMBER_HISTORY_PERMS
        )


async def test_family_member_history_org_less_token_rejected(client):
    """An org-less token is rejected with 403 on create and list."""
    p_id = await create_test_patient(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=FAMILY_MEMBER_HISTORY_PERMS,
    )
    try:
        resp = await client.post(
            BASE + "/",
            json=minimal_family_member_history(p_id),
        )
        assert resp.status_code == 403, resp.text

        list_resp = await client.get(BASE + "/")
        assert list_resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=FAMILY_MEMBER_HISTORY_PERMS
        )

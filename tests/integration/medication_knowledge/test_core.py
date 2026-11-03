"""Core MedicationKnowledge endpoint coverage.

MedicationKnowledge has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_medication_knowledge,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_medication_knowledge,
)
from tests.integration.medication_knowledge.support import (
    BASE,
    FHIR_ACCEPT,
    create_medication_knowledge,
    create_test_medication,
    create_test_organization,
    full_medication_knowledge,
    minimal_medication_knowledge,
)

MEDICATION_KNOWLEDGE_PERMS = [
    "medication_knowledge:create",
    "medication_knowledge:read",
    "medication_knowledge:update",
    "medication_knowledge:delete",
    "organization:create",
    "organization:read",
    "medication:create",
    "medication:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_medication_knowledge_minimal(client):
    resp = await client.post(BASE + "/", json=minimal_medication_knowledge())
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_medication_knowledge(data)
    assert data["status"] == "active"
    assert data["code"]["text"] == "Amoxicillin 500 MG Oral Capsule"


async def test_create_medication_knowledge_full(client):
    org_id = await create_test_organization(client)
    med_id = await create_test_medication(client)

    payload = full_medication_knowledge(org_id=org_id, assoc_med_id=med_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_medication_knowledge(data)
    assert data["status"] == "active"
    assert data["manufacturer"]["reference"] == f"Organization/{org_id}"
    assert data["manufacturer"]["display"] == "Pharma Corp"
    assert data["dose_form"]["text"] == "Capsule"
    assert data["amount"]["value"] == 500.0
    assert data["synonym"] == ["Amoxil", "Trimox"]
    assert data["packaging"]["type"]["text"] == "Bottle"
    assert data["packaging"]["quantity"]["value"] == 100.0
    assert len(data["product_type"]) == 1
    assert data["product_type"][0]["text"] == "Prescription Only"
    assert len(data["ingredient"]) == 1
    assert data["ingredient"][0]["item_codeable_concept"]["text"] == "Amoxicillin"
    assert len(data["intended_route"]) == 1
    assert data["intended_route"][0]["text"] == "Oral"
    assert len(data["cost"]) == 1
    assert data["cost"][0]["cost"]["value"] == 15.5
    assert len(data["monitoring_program"]) == 1
    assert data["monitoring_program"][0]["name"] == "Safe Use Program"
    assert len(data["administration_guidelines"]) == 1
    assert (
        data["administration_guidelines"][0]["indication_codeable_concept"]["text"]
        == "Bacterial Infection"
    )
    assert len(data["medicine_classification"]) == 1
    assert len(data["drug_characteristic"]) == 1
    assert data["drug_characteristic"][0]["value_string"] == "Yellow / Maroon"
    assert len(data["associated_medication"]) == 1
    assert data["associated_medication"][0]["reference"] == f"Medication/{med_id}"
    assert len(data["regulatory"]) == 1
    assert (
        data["regulatory"][0]["regulatory_authority"]["reference"]
        == f"Organization/{org_id}"
    )


async def test_create_medication_knowledge_fhir_format(client):
    resp = await client.post(
        BASE + "/",
        json=minimal_medication_knowledge(),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    assert resp.headers["content-type"].startswith("application/fhir+json")
    data = resp.json()
    assert_fhir_medication_knowledge(data)
    assert data["resourceType"] == "MedicationKnowledge"
    assert data["status"] == "active"
    assert data["code"]["text"] == "Amoxicillin 500 MG Oral Capsule"


async def test_create_medication_knowledge_extra_fields_forbidden(client):
    payload = {
        **minimal_medication_knowledge(),
        "user_id": "usr-123",  # forbidden
    }
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422


async def test_create_medication_knowledge_nonexistent_reference(client):
    payload = {
        **minimal_medication_knowledge(),
        "manufacturer": "Organization/999999",
    }
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422


# ── Read ─────────────────────────────────────────────────────────────────


async def test_read_medication_knowledge_plain(client):
    created = await create_medication_knowledge(client)
    mk_id = created["id"]

    resp = await client.get(f"{BASE}/{mk_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_medication_knowledge(data, id=mk_id)
    assert data["status"] == "active"


async def test_read_medication_knowledge_fhir(client):
    created = await create_medication_knowledge(client)
    mk_id = created["id"]

    resp = await client.get(f"{BASE}/{mk_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("application/fhir+json")
    data = resp.json()
    assert_fhir_medication_knowledge(data)
    assert data["id"] == str(mk_id)


async def test_read_medication_knowledge_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_medication_knowledge_field_updates(client):
    created = await create_medication_knowledge(client)
    mk_id = created["id"]

    patch_payload = {
        "status": "inactive",
        "synonym": ["Updated Synonym"],
    }
    resp = await client.patch(f"{BASE}/{mk_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_medication_knowledge(data, id=mk_id)
    assert data["status"] == "inactive"
    assert data["synonym"] == ["Updated Synonym"]


async def test_patch_medication_knowledge_sub_resource_replace(client):
    created = await create_medication_knowledge(client)
    mk_id = created["id"]

    patch_payload = {
        "cost": [
            {
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/medication-knowledge-cost-type",
                            "code": "retail",
                            "display": "Retail Price",
                        }
                    ],
                    "text": "Retail",
                },
                "cost": {
                    "value": 25.0,
                    "currency": "USD",
                },
            }
        ]
    }
    resp = await client.patch(f"{BASE}/{mk_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["cost"]) == 1
    assert data["cost"][0]["cost"]["value"] == 25.0


async def test_patch_medication_knowledge_fhir_format(client):
    created = await create_medication_knowledge(client)
    mk_id = created["id"]

    resp = await client.patch(
        f"{BASE}/{mk_id}",
        json={"status": "inactive"},
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("application/fhir+json")
    data = resp.json()
    assert_fhir_medication_knowledge(data)
    assert data["status"] == "inactive"


async def test_patch_medication_knowledge_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "inactive"})
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_medication_knowledge_plain(client):
    await create_medication_knowledge(client)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    assert data["total"] >= 1
    assert len(data["data"]) >= 1


async def test_list_medication_knowledge_fhir(client):
    await create_medication_knowledge(client)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("application/fhir+json")
    data = resp.json()
    assert_fhir_bundle(data)
    assert data["total"] >= 1


async def test_list_medication_knowledge_filter_status(client):
    await create_medication_knowledge(client, status="active")
    resp = await client.get(BASE + "/?status=active")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert all(item["status"] == "active" for item in data["data"])


async def test_list_medication_knowledge_filter_code(client):
    created = await create_medication_knowledge(client)
    resp = await client.get(BASE + "/?code=308182")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert any(item["id"] == created["id"] for item in data["data"])


async def test_list_medication_knowledge_filter_dose_form(client):
    created = await create_medication_knowledge(
        client,
        dose_form={
            "text": "Syrup",
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "385018001",
                    "display": "Oral syrup",
                }
            ],
        },
    )
    resp = await client.get(BASE + "/?dose_form=Syrup")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert any(item["id"] == created["id"] for item in data["data"])


async def test_list_medication_knowledge_pagination(client):
    for _ in range(3):
        await create_medication_knowledge(client)
    resp = await client.get(BASE + "/?limit=2&offset=0")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["data"]) <= 2


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_medication_knowledge(client):
    created = await create_medication_knowledge(client)
    mk_id = created["id"]

    resp = await client.delete(f"{BASE}/{mk_id}")
    assert resp.status_code == 204

    # Verify 404 after delete
    get_resp = await client.get(f"{BASE}/{mk_id}")
    assert get_resp.status_code == 404


async def test_delete_medication_knowledge_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Auth & Scoping ───────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    # Org A creates
    created = await create_medication_knowledge(client)
    mk_id = created["id"]

    # Switch to Org B
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-other",
        permissions=MEDICATION_KNOWLEDGE_PERMS,
    )
    try:
        # Get -> 404
        get_resp = await client.get(f"{BASE}/{mk_id}")
        assert get_resp.status_code == 404

        # Patch -> 404
        patch_resp = await client.patch(f"{BASE}/{mk_id}", json={"status": "inactive"})
        assert patch_resp.status_code == 404

        # Delete -> 404
        delete_resp = await client.delete(f"{BASE}/{mk_id}")
        assert delete_resp.status_code == 404

        # List -> does not include Org A's record
        list_resp = await client.get(BASE + "/")
        assert list_resp.status_code == 200
        assert all(item["id"] != mk_id for item in list_resp.json()["data"])
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=MEDICATION_KNOWLEDGE_PERMS
        )


async def test_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=MEDICATION_KNOWLEDGE_PERMS,
    )
    try:
        resp = await client.post(BASE + "/", json=minimal_medication_knowledge())
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=MEDICATION_KNOWLEDGE_PERMS
        )

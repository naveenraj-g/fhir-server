"""Core Medication endpoint coverage.

Medication has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_medication,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_medication,
)
from tests.integration.medication.support import (
    BASE,
    FHIR_ACCEPT,
    create_medication,
    create_test_organization,
    full_medication,
    minimal_medication,
)

MEDICATION_PERMS = [
    "medication:create",
    "medication:read",
    "medication:update",
    "medication:delete",
    "organization:create",
    "organization:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_medication_minimal(client):
    resp = await client.post(BASE + "/", json=minimal_medication())
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_medication(data)
    assert data["status"] == "active"
    assert data["code"]["text"] == "Amoxicillin 500 MG Oral Tablet"


async def test_create_medication_full(client):
    org_id = await create_test_organization(client)
    # create a second medication to use as reference ingredient
    ing_med = await create_medication(client)
    ing_med_id = ing_med["id"]

    payload = full_medication(org_id=org_id, ingredient_med_id=ing_med_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_medication(data)
    assert data["status"] == "active"
    assert data["manufacturer"]["reference"] == f"Organization/{org_id}"
    assert data["manufacturer"]["display"] == "Acme Pharmaceuticals"
    assert data["form"]["text"] == "Tablet"
    assert data["amount"]["numerator"]["value"] == 1.0
    assert data["amount"]["numerator"]["unit"] == "TAB"
    assert data["amount"]["denominator"]["value"] == 1.0
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "MED-12345"
    assert len(data["ingredient"]) == 2
    assert data["ingredient"][0]["item_codeable_concept"]["text"] == "Amoxicillin"
    assert data["ingredient"][1]["item_reference"]["reference"] == f"Medication/{ing_med_id}"
    assert data["batch"]["lot_number"] == "LOT-9876"


async def test_create_medication_fhir_format(client):
    resp = await client.post(
        BASE + "/",
        json=minimal_medication(),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    assert resp.headers["content-type"].startswith("application/fhir+json")
    data = resp.json()
    assert_fhir_medication(data)
    assert data["resourceType"] == "Medication"
    assert data["status"] == "active"
    assert data["code"]["text"] == "Amoxicillin 500 MG Oral Tablet"


async def test_create_medication_extra_fields_forbidden(client):
    payload = {
        **minimal_medication(),
        "user_id": "usr-123",  # forbidden
    }
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422


async def test_create_medication_invalid_reference(client):
    payload = {
        **minimal_medication(),
        "manufacturer": "Organization/999999",
    }
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_medication_plain(client):
    created = await create_medication(client)
    med_id = created["id"]

    resp = await client.get(f"{BASE}/{med_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_medication(data)
    assert data["id"] == med_id
    assert data["status"] == "active"


async def test_get_medication_fhir(client):
    created = await create_medication(client)
    med_id = created["id"]

    resp = await client.get(f"{BASE}/{med_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("application/fhir+json")
    data = resp.json()
    assert_fhir_medication(data)
    assert data["id"] == str(med_id)
    assert data["resourceType"] == "Medication"


async def test_get_medication_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_medication_fields(client):
    created = await create_medication(client)
    med_id = created["id"]

    resp = await client.patch(
        f"{BASE}/{med_id}",
        json={"status": "inactive"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_medication(data)
    assert data["status"] == "inactive"


async def test_patch_medication_sub_resources_wholesale_replace(client):
    created = await create_medication(client)
    med_id = created["id"]

    resp = await client.patch(
        f"{BASE}/{med_id}",
        json={
            "identifier": [
                {
                    "system": "http://example.org/new-id",
                    "value": "NEW-VAL-1",
                }
            ],
            "batch": {"lot_number": "NEW-LOT"},
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "NEW-VAL-1"
    assert data["batch"]["lot_number"] == "NEW-LOT"


async def test_patch_medication_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "inactive"})
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_medications_plain(client):
    await create_medication(client)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    assert len(data["data"]) >= 1
    assert_plain_medication(data["data"][0])


async def test_list_medications_fhir_bundle(client):
    await create_medication(client)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"].startswith("application/fhir+json")
    data = resp.json()
    assert_fhir_bundle(data)
    assert data["type"] == "searchset"
    assert len(data["entry"]) >= 1
    assert_fhir_medication(data["entry"][0]["resource"])


async def test_list_medications_filter_by_status(client):
    m_active = await create_medication(client, {"status": "active"})
    m_inactive = await create_medication(client, {"status": "inactive"})

    resp = await client.get(BASE + "/?status=inactive")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert m_inactive["id"] in ids
    assert m_active["id"] not in ids


async def test_list_medications_filter_by_code(client):
    payload = {
        "status": "active",
        "code": {
            "coding": [
                {
                    "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                    "code": "197361",
                    "display": "Acyclovir 400 MG Oral Tablet",
                }
            ],
            "text": "Acyclovir 400 MG Oral Tablet",
        },
    }
    created = await create_medication(client, payload)

    resp = await client.get(BASE + "/?code=197361")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert created["id"] in ids


async def test_list_medications_filter_by_form(client):
    payload = {
        "status": "active",
        "form": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "385268001",
                    "display": "Oral solution",
                }
            ],
            "text": "Oral solution",
        },
    }
    created = await create_medication(client, payload)

    resp = await client.get(BASE + "/?form=385268001")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert created["id"] in ids


async def test_list_medications_filter_by_ingredient(client):
    ing_med = await create_medication(client)
    ing_id = ing_med["id"]
    payload = {
        "status": "active",
        "ingredient": [
            {
                "item_reference": f"Medication/{ing_id}",
                "is_active": True,
            }
        ],
    }
    created = await create_medication(client, payload)

    resp = await client.get(f"{BASE}/?ingredient=Medication/{ing_id}")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert created["id"] in ids


async def test_list_medications_filter_by_lot_number(client):
    payload = {
        "status": "active",
        "batch": {"lot_number": "LOT-SPECIAL-99"},
    }
    created = await create_medication(client, payload)

    resp = await client.get(BASE + "/?lot-number=LOT-SPECIAL-99")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert created["id"] in ids


async def test_list_medications_pagination(client):
    await create_medication(client)
    await create_medication(client)

    resp = await client.get(BASE + "/?limit=1&offset=0")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["data"]) == 1
    assert data["limit"] == 1
    assert data["offset"] == 0
    assert data["total"] >= 2


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_medication(client):
    created = await create_medication(client)
    med_id = created["id"]

    del_resp = await client.delete(f"{BASE}/{med_id}")
    assert del_resp.status_code == 204, del_resp.text

    get_resp = await client.get(f"{BASE}/{med_id}")
    assert get_resp.status_code == 404


async def test_delete_medication_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Multi-Tenancy & Auth ──────────────────────────────────────────────────


async def test_medication_cross_org_isolation(client):
    """Resource created under org-1 returns 404 (not 403) to a caller in org-2."""
    created = await create_medication(client)
    med_id = created["id"]

    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="different-org-id",
        permissions=MEDICATION_PERMS,
    )
    try:
        resp = await client.get(f"{BASE}/{med_id}")
        assert resp.status_code == 404, resp.text
        assert_operation_outcome(resp.json(), 404, resp.status_code)

        patch_resp = await client.patch(
            f"{BASE}/{med_id}", json={"status": "inactive"}
        )
        assert patch_resp.status_code == 404

        del_resp = await client.delete(f"{BASE}/{med_id}")
        assert del_resp.status_code == 404
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=MEDICATION_PERMS
        )


async def test_medication_org_less_token_rejected(client):
    """An org-less token is rejected with 403 on create and list."""
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=MEDICATION_PERMS,
    )
    try:
        resp = await client.post(
            BASE + "/",
            json=minimal_medication(),
        )
        assert resp.status_code == 403, resp.text

        list_resp = await client.get(BASE + "/")
        assert list_resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=MEDICATION_PERMS
        )

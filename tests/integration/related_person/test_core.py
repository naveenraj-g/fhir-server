"""Core RelatedPerson endpoint coverage.

RelatedPerson has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_related_person,
    assert_paginated,
    assert_plain_related_person,
)
from tests.integration.related_person.support import (
    BASE,
    FHIR_ACCEPT,
    create_test_organization,
    create_test_patient,
    full_related_person,
    minimal_related_person,
)

RELATED_PERSON_PERMS = [
    "related_person:create",
    "related_person:read",
    "related_person:update",
    "related_person:delete",
    "patient:create",
    "patient:read",
    "organization:create",
    "organization:read",
]


async def create_related_person(client, patient_id: int) -> int:
    """Helper to create a minimal RelatedPerson and return public ID."""
    resp = await client.post(BASE + "/", json=minimal_related_person(patient_id))
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_related_person_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_related_person(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_related_person(data)
    assert data["patient_reference"] == f"Patient/{p_id}"
    assert data["id"] >= 300000


async def test_create_related_person_full(client):
    p_id = await create_test_patient(client)
    org_id = await create_test_organization(client)
    payload = full_related_person(p_id, org_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_related_person(data)
    assert data["active"] is True
    assert data["gender"] == "female"
    assert data["birth_date"] == "1980-05-21"
    assert data["patient_reference"] == f"Patient/{p_id}"
    assert len(data["relationships"]) == 1
    assert data["relationships"][0]["text"] == "Mother"
    assert len(data["names"]) == 1
    assert data["names"][0]["family"] == "Smith"
    assert len(data["telecoms"]) == 1
    assert len(data["addresses"]) == 1
    assert len(data["photos"]) == 1
    assert len(data["communications"]) == 1
    assert len(data["identifiers"]) == 1


async def test_create_related_person_fhir_format(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/", json=minimal_related_person(p_id), headers=FHIR_ACCEPT
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_related_person(data)
    assert data["patient"]["reference"] == f"Patient/{p_id}"
    assert int(data["id"]) >= 300000


async def test_create_related_person_unknown_patient_422(client):
    payload = minimal_related_person(99999999)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_related_person_plain(client):
    p_id = await create_test_patient(client)
    rp_id = await create_related_person(client, p_id)
    resp = await client.get(f"{BASE}/{rp_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_related_person(data)
    assert data["id"] == rp_id
    assert data["patient_reference"] == f"Patient/{p_id}"


async def test_get_related_person_fhir(client):
    p_id = await create_test_patient(client)
    rp_id = await create_related_person(client, p_id)
    resp = await client.get(f"{BASE}/{rp_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_related_person(data)
    assert data["id"] == str(rp_id)
    assert data["patient"]["reference"] == f"Patient/{p_id}"


async def test_get_related_person_not_found(client):
    resp = await client.get(f"{BASE}/99999999")
    assert resp.status_code == 404


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_related_person_scalar(client):
    p_id = await create_test_patient(client)
    rp_id = await create_related_person(client, p_id)
    resp = await client.patch(
        f"{BASE}/{rp_id}",
        json={"active": False, "gender": "male", "birth_date": "1990-01-01"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["active"] is False
    assert data["gender"] == "male"
    assert data["birth_date"] == "1990-01-01"


async def test_patch_related_person_sub_list_replace(client):
    p_id = await create_test_patient(client)
    rp_id = await create_related_person(client, p_id)
    new_telecom = [{"system": "email", "value": "test@example.com", "use": "work"}]
    resp = await client.patch(f"{BASE}/{rp_id}", json={"telecom": new_telecom})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["telecoms"]) == 1
    assert data["telecoms"][0]["system"] == "email"
    assert data["telecoms"][0]["value"] == "test@example.com"


async def test_patch_related_person_not_found(client):
    resp = await client.patch(f"{BASE}/99999999", json={"active": False})
    assert resp.status_code == 404


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_related_person_plain(client):
    p_id = await create_test_patient(client)
    rp_id = await create_related_person(client, p_id)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    ids = [item["id"] for item in data["data"]]
    assert rp_id in ids


async def test_list_related_person_fhir(client):
    p_id = await create_test_patient(client)
    rp_id = await create_related_person(client, p_id)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    entry_ids = [e["resource"]["id"] for e in data.get("entry", [])]
    assert str(rp_id) in entry_ids


async def test_list_related_person_filter_patient(client):
    p1 = await create_test_patient(client)
    p2 = await create_test_patient(client)
    rp1 = await create_related_person(client, p1)
    rp2 = await create_related_person(client, p2)

    resp = await client.get(f"{BASE}/?patient=Patient/{p1}")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert rp1 in ids
    assert rp2 not in ids


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_related_person(client):
    p_id = await create_test_patient(client)
    rp_id = await create_related_person(client, p_id)
    resp = await client.delete(f"{BASE}/{rp_id}")
    assert resp.status_code == 204

    resp2 = await client.get(f"{BASE}/{rp_id}")
    assert resp2.status_code == 404


# ── Auth & Tenancy ───────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    p_id = await create_test_patient(client)
    rp_id = await create_related_person(client, p_id)

    # Switch to different organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="other-org",
        permissions=RELATED_PERSON_PERMS,
    )

    resp = await client.get(f"{BASE}/{rp_id}")
    assert resp.status_code == 404

    resp_patch = await client.patch(f"{BASE}/{rp_id}", json={"active": False})
    assert resp_patch.status_code == 404

    resp_del = await client.delete(f"{BASE}/{rp_id}")
    assert resp_del.status_code == 404

    resp_list = await client.get(BASE + "/")
    assert resp_list.status_code == 200
    ids = [item["id"] for item in resp_list.json()["data"]]
    assert rp_id not in ids


async def test_orgless_token_rejected_403(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=RELATED_PERSON_PERMS,
    )
    resp = await client.post(BASE + "/", json=minimal_related_person(10001))
    assert resp.status_code == 403

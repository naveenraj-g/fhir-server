"""Core Flag endpoint coverage.

Flag has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_flag,
    assert_paginated,
    assert_plain_flag,
)
from tests.integration.flag.support import (
    BASE,
    FHIR_ACCEPT,
    create_test_encounter,
    create_test_organization,
    create_test_patient,
    create_test_practitioner,
    full_flag,
    minimal_flag,
)

FLAG_PERMS = [
    "flag:create",
    "flag:read",
    "flag:update",
    "flag:delete",
    "patient:create",
    "patient:read",
    "organization:create",
    "organization:read",
    "encounter:create",
    "encounter:read",
    "practitioner:create",
    "practitioner:read",
]


async def create_flag(client, patient_id: int) -> int:
    """Helper to create a minimal Flag and return public ID."""
    resp = await client.post(BASE + "/", json=minimal_flag(patient_id))
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_flag_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_flag(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_flag(data)
    assert data["subject_reference"] == f"Patient/{p_id}"
    assert data["status"] == "active"
    assert data["id"] >= 450000


async def test_create_flag_full(client):
    p_id = await create_test_patient(client)
    enc_id = await create_test_encounter(client, p_id)
    pr_id = await create_test_practitioner(client)
    org_id = await create_test_organization(client)
    payload = full_flag(p_id, enc_id, pr_id, org_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_flag(data)
    assert data["status"] == "active"
    assert data["subject_reference"] == f"Patient/{p_id}"
    assert data["encounter_reference"] == f"Encounter/{enc_id}"
    assert data["author_reference"] == f"Practitioner/{pr_id}"
    assert len(data["categories"]) == 1
    assert data["categories"][0]["text"] == "Clinical"
    assert len(data["code_codings"]) == 1
    assert len(data["identifiers"]) == 1
    assert data["identifiers"][0]["value"] == "FLAG12345"


async def test_create_flag_fhir_format(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/", json=minimal_flag(p_id), headers=FHIR_ACCEPT
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_flag(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "active"
    assert int(data["id"]) >= 450000


async def test_create_flag_unknown_subject_422(client):
    payload = minimal_flag(99999999)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_flag_plain(client):
    p_id = await create_test_patient(client)
    fl_id = await create_flag(client, p_id)
    resp = await client.get(f"{BASE}/{fl_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_flag(data)
    assert data["id"] == fl_id
    assert data["subject_reference"] == f"Patient/{p_id}"


async def test_get_flag_fhir(client):
    p_id = await create_test_patient(client)
    fl_id = await create_flag(client, p_id)
    resp = await client.get(f"{BASE}/{fl_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_flag(data)
    assert data["id"] == str(fl_id)
    assert data["subject"]["reference"] == f"Patient/{p_id}"


async def test_get_flag_not_found(client):
    resp = await client.get(f"{BASE}/99999999")
    assert resp.status_code == 404


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_flag_scalar(client):
    p_id = await create_test_patient(client)
    fl_id = await create_flag(client, p_id)
    resp = await client.patch(
        f"{BASE}/{fl_id}",
        json={"status": "inactive", "code_text": "Updated flag text"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "inactive"
    assert data["code_text"] == "Updated flag text"


async def test_patch_flag_sub_list_replace(client):
    p_id = await create_test_patient(client)
    fl_id = await create_flag(client, p_id)
    new_categories = [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/flag-category",
                    "code": "admin",
                    "display": "Administrative",
                }
            ],
            "text": "Administrative",
        }
    ]
    resp = await client.patch(f"{BASE}/{fl_id}", json={"category": new_categories})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["categories"]) == 1
    assert data["categories"][0]["text"] == "Administrative"


async def test_patch_flag_not_found(client):
    resp = await client.patch(f"{BASE}/99999999", json={"status": "inactive"})
    assert resp.status_code == 404


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_flag_plain(client):
    p_id = await create_test_patient(client)
    fl_id = await create_flag(client, p_id)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    ids = [item["id"] for item in data["data"]]
    assert fl_id in ids


async def test_list_flag_fhir(client):
    p_id = await create_test_patient(client)
    fl_id = await create_flag(client, p_id)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    entry_ids = [e["resource"]["id"] for e in data.get("entry", [])]
    assert str(fl_id) in entry_ids


async def test_list_flag_filter_subject(client):
    p1 = await create_test_patient(client)
    p2 = await create_test_patient(client)
    fl1 = await create_flag(client, p1)
    fl2 = await create_flag(client, p2)

    resp = await client.get(f"{BASE}/?subject=Patient/{p1}")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert fl1 in ids
    assert fl2 not in ids


async def test_list_flag_filter_status(client):
    p_id = await create_test_patient(client)
    fl1 = await create_flag(client, p_id)
    await client.patch(f"{BASE}/{fl1}", json={"status": "inactive"})
    fl2 = await create_flag(client, p_id)

    resp = await client.get(f"{BASE}/?status=active")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert fl2 in ids
    assert fl1 not in ids


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_flag(client):
    p_id = await create_test_patient(client)
    fl_id = await create_flag(client, p_id)
    resp = await client.delete(f"{BASE}/{fl_id}")
    assert resp.status_code == 204

    resp2 = await client.get(f"{BASE}/{fl_id}")
    assert resp2.status_code == 404


# ── Auth & Tenancy ───────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    p_id = await create_test_patient(client)
    fl_id = await create_flag(client, p_id)

    # Switch to different organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="other-org",
        permissions=FLAG_PERMS,
    )

    resp = await client.get(f"{BASE}/{fl_id}")
    assert resp.status_code == 404

    resp_patch = await client.patch(f"{BASE}/{fl_id}", json={"status": "inactive"})
    assert resp_patch.status_code == 404

    resp_del = await client.delete(f"{BASE}/{fl_id}")
    assert resp_del.status_code == 404

    resp_list = await client.get(BASE + "/")
    assert resp_list.status_code == 200
    ids = [item["id"] for item in resp_list.json()["data"]]
    assert fl_id not in ids


async def test_orgless_token_rejected_403(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=FLAG_PERMS,
    )
    resp = await client.post(BASE + "/", json=minimal_flag(10001))
    assert resp.status_code == 403

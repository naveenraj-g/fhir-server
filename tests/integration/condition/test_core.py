"""Core condition endpoint coverage.

Condition has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
Every supplied sub-resource list on create/patch (identifier, category, body_site,
stage, evidence, note) replaces corresponding rows wholesale.

This file holds:
- create (minimal + full nested payload, FHIR format, validation, reference check)
- read (plain + FHIR, not found)
- patch (field updates, sub-list replace, empty list clear, not found)
- list (plain, FHIR bundle, filters, pagination)
- delete
- auth: cross-org isolation and org-less rejection
"""

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import (
    assert_fhir_bundle,
    assert_fhir_condition,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_condition,
)
from tests.integration.condition.support import (
    BASE,
    FHIR_ACCEPT,
    create_condition,
    create_test_patient,
    full_condition,
    minimal_condition,
)

CONDITION_PERMS = [
    "condition:create",
    "condition:read",
    "condition:update",
    "condition:delete",
    "patient:create",
    "patient:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_condition_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_condition(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_condition(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["code_text"] == "Hypertension"


async def test_create_condition_full(client):
    p_id = await create_test_patient(client)
    payload = full_condition(p_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_condition(data)
    assert data["clinical_status_text"] == "Active"
    assert data["verification_status_text"] == "Confirmed"
    assert data["severity_text"] == "Severe"
    assert data["code_text"] == "Essential hypertension"
    assert len(data["categories"]) == 1
    assert len(data["body_sites"]) == 1
    assert len(data["stages"]) == 1
    assert len(data["evidence"]) == 1
    assert len(data["notes"]) == 1
    assert data["notes"][0]["text"] == "Prescribed ACE inhibitors. Monitor blood pressure daily."


async def test_create_condition_fhir_format(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/", json=minimal_condition(p_id), headers=FHIR_ACCEPT
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_condition(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"


async def test_create_condition_validation_extra_forbidden(client):
    p_id = await create_test_patient(client)
    payload = minimal_condition(p_id)
    payload["unknown_field"] = "invalid"
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text


async def test_create_condition_unresolved_reference_422(client):
    payload = {
        "subject": {"reference": "Patient/999999"},
        "code": {"text": "Unknown"},
    }
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text
    assert_operation_outcome(resp.json(), 422, resp.status_code)


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_condition_plain(client):
    cond_id = await create_condition(client)
    resp = await client.get(f"{BASE}/{cond_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_condition(data, id=cond_id)


async def test_get_condition_fhir(client):
    cond_id = await create_condition(client)
    resp = await client.get(f"{BASE}/{cond_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_condition(data, id=str(cond_id))


async def test_get_condition_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_condition_fields(client):
    p_id = await create_test_patient(client)
    cond_id = await create_condition(client, minimal_condition(p_id))

    resp = await client.patch(
        f"{BASE}/{cond_id}",
        json={
            "severity": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "24484000",
                        "display": "Severe",
                    }
                ],
                "text": "Severe",
            }
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["severity_text"] == "Severe"
    assert data["severity_codings"][0]["code"] == "24484000"


async def test_patch_condition_replace_notes(client):
    p_id = await create_test_patient(client)
    cond_id = await create_condition(client, full_condition(p_id))

    new_notes = [
        {"author_string": "Dr. Strange", "text": "Patient condition improved"}
    ]
    resp = await client.patch(f"{BASE}/{cond_id}", json={"note": new_notes})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["notes"]) == 1
    assert data["notes"][0]["author_string"] == "Dr. Strange"
    assert data["notes"][0]["text"] == "Patient condition improved"


async def test_patch_condition_empty_list_clears(client):
    p_id = await create_test_patient(client)
    cond_id = await create_condition(client, full_condition(p_id))

    resp = await client.patch(f"{BASE}/{cond_id}", json={"note": []})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["notes"] == []


async def test_patch_condition_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"severity": {"text": "Mild"}})
    assert resp.status_code == 404, resp.text


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_conditions_plain(client):
    await create_condition(client)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data, min_total=1)


async def test_list_conditions_fhir_bundle(client):
    await create_condition(client)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data, min_total=1)
    assert data["entry"][0]["resource"]["resourceType"] == "Condition"


async def test_list_conditions_filter_by_code(client):
    p_id = await create_test_patient(client)
    await create_condition(client, minimal_condition(p_id))

    resp = await client.get(f"{BASE}/?code=38341003")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] >= 1
    assert all(
        any(c["code"] == "38341003" for c in row["code_codings"])
        for row in data["data"]
    )


async def test_list_conditions_filter_by_subject(client):
    p_id = await create_test_patient(client)
    await create_condition(client, minimal_condition(p_id))

    resp = await client.get(f"{BASE}/?subject=Patient/{p_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] >= 1
    assert all(row["subject"]["reference"] == f"Patient/{p_id}" for row in data["data"])


async def test_list_conditions_pagination(client):
    p_id = await create_test_patient(client)
    await create_condition(client, minimal_condition(p_id))
    await create_condition(client, minimal_condition(p_id))

    resp = await client.get(f"{BASE}/?limit=1&offset=0")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["data"]) == 1
    assert data["limit"] == 1
    assert data["offset"] == 0


# ── Me ───────────────────────────────────────────────────────────────────


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_condition(client):
    cond_id = await create_condition(client)
    del_resp = await client.delete(f"{BASE}/{cond_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"{BASE}/{cond_id}")
    assert get_resp.status_code == 404


async def test_delete_condition_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert resp.status_code == 404


# ── Auth & Isolation ─────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    # Org A creates a condition
    cond_id = await create_condition(client)

    # Org B attempts to read
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-other", permissions=CONDITION_PERMS
    )
    resp = await client.get(f"{BASE}/{cond_id}")
    assert resp.status_code == 404, "Cross-org read must 404 without leaking existence"

    # Org B attempts to patch
    patch_resp = await client.patch(
        f"{BASE}/{cond_id}", json={"severity": {"text": "Mild"}}
    )
    assert patch_resp.status_code == 404

    # Org B attempts to delete
    del_resp = await client.delete(f"{BASE}/{cond_id}")
    assert del_resp.status_code == 404


async def test_org_less_actor_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None, permissions=CONDITION_PERMS
    )
    resp = await client.post(
        BASE + "/", json={"subject": {"reference": "Patient/10001"}}
    )
    assert resp.status_code == 403

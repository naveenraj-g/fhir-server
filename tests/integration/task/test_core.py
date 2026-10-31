"""Core Task endpoint coverage.

Task has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_task,
    assert_paginated,
    assert_plain_task,
)
from tests.integration.task.support import (
    BASE,
    FHIR_ACCEPT,
    create_test_encounter,
    create_test_location,
    create_test_organization,
    create_test_patient,
    create_test_practitioner,
    full_task,
    minimal_task,
)

TASK_PERMS = [
    "task:create",
    "task:read",
    "task:update",
    "task:delete",
    "patient:create",
    "patient:read",
    "organization:create",
    "organization:read",
    "encounter:create",
    "encounter:read",
    "practitioner:create",
    "practitioner:read",
    "location:create",
    "location:read",
]


async def create_task(client, patient_id: int) -> int:
    """Helper to create a minimal Task and return public ID."""
    resp = await client.post(BASE + "/", json=minimal_task(patient_id))
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_task_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_task(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_task(data)
    assert data["for_reference"] == f"Patient/{p_id}"
    assert data["status"] == "requested"
    assert data["intent"] == "order"
    assert data["id"] >= 280000


async def test_create_task_full(client):
    p_id = await create_test_patient(client)
    enc_id = await create_test_encounter(client, p_id)
    pr_id = await create_test_practitioner(client)
    loc_id = await create_test_location(client)
    org_id = await create_test_organization(client)
    payload = full_task(p_id, enc_id, pr_id, pr_id, loc_id, org_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_task(data)
    assert data["status"] == "requested"
    assert data["intent"] == "order"
    assert data["for_reference"] == f"Patient/{p_id}"
    assert data["encounter_reference"] == f"Encounter/{enc_id}"
    assert data["requester_reference"] == f"Practitioner/{pr_id}"
    assert data["owner_reference"] == f"Practitioner/{pr_id}"
    assert data["location_reference"] == f"Location/{loc_id}"
    assert len(data["code_codings"]) == 1
    assert len(data["identifiers"]) == 1
    assert data["identifiers"][0]["value"] == "TASK-12345"
    assert len(data["inputs"]) == 1
    assert data["inputs"][0]["value_string"] == "Sample instructions"
    assert len(data["outputs"]) == 1
    assert data["outputs"][0]["value_string"] == "Approved by supervisor"
    assert len(data["notes"]) == 1
    assert data["notes"][0]["text"] == "All vitals checked and normal."


async def test_create_task_fhir_format(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/", json=minimal_task(p_id), headers=FHIR_ACCEPT
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_task(data)
    assert data["for"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "requested"
    assert data["intent"] == "order"
    assert int(data["id"]) >= 280000


async def test_create_task_unknown_for_422(client):
    payload = minimal_task(99999999)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_task_plain(client):
    p_id = await create_test_patient(client)
    t_id = await create_task(client, p_id)
    resp = await client.get(f"{BASE}/{t_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_task(data)
    assert data["id"] == t_id
    assert data["for_reference"] == f"Patient/{p_id}"


async def test_get_task_fhir(client):
    p_id = await create_test_patient(client)
    t_id = await create_task(client, p_id)
    resp = await client.get(f"{BASE}/{t_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_task(data)
    assert data["id"] == str(t_id)
    assert data["for"]["reference"] == f"Patient/{p_id}"


async def test_get_task_not_found(client):
    resp = await client.get(f"{BASE}/99999999")
    assert resp.status_code == 404


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_task_scalar(client):
    p_id = await create_test_patient(client)
    t_id = await create_task(client, p_id)
    resp = await client.patch(
        f"{BASE}/{t_id}",
        json={"status": "in-progress", "description": "Updated task description"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "in-progress"
    assert data["description"] == "Updated task description"


async def test_patch_task_sub_list_replace(client):
    p_id = await create_test_patient(client)
    t_id = await create_task(client, p_id)
    new_notes = [
        {
            "author_string": "Doctor Bob",
            "text": "Reviewed and confirmed patient identity.",
        }
    ]
    resp = await client.patch(f"{BASE}/{t_id}", json={"note": new_notes})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["notes"]) == 1
    assert data["notes"][0]["text"] == "Reviewed and confirmed patient identity."


async def test_patch_task_not_found(client):
    resp = await client.patch(f"{BASE}/99999999", json={"status": "completed"})
    assert resp.status_code == 404


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_task_plain(client):
    p_id = await create_test_patient(client)
    t_id = await create_task(client, p_id)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    ids = [item["id"] for item in data["data"]]
    assert t_id in ids


async def test_list_task_fhir(client):
    p_id = await create_test_patient(client)
    t_id = await create_task(client, p_id)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    entry_ids = [e["resource"]["id"] for e in data.get("entry", [])]
    assert str(t_id) in entry_ids


async def test_list_task_filter_for(client):
    p1 = await create_test_patient(client)
    p2 = await create_test_patient(client)
    t1 = await create_task(client, p1)
    t2 = await create_task(client, p2)

    resp = await client.get(f"{BASE}/?for=Patient/{p1}")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert t1 in ids
    assert t2 not in ids


async def test_list_task_filter_status(client):
    p_id = await create_test_patient(client)
    t1 = await create_task(client, p_id)
    await client.patch(f"{BASE}/{t1}", json={"status": "completed"})
    t2 = await create_task(client, p_id)

    resp = await client.get(f"{BASE}/?status=requested")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert t2 in ids
    assert t1 not in ids


async def test_list_task_filter_intent(client):
    p_id = await create_test_patient(client)
    t1 = await create_task(client, p_id)

    resp = await client.get(f"{BASE}/?intent=order")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert t1 in ids

    resp_none = await client.get(f"{BASE}/?intent=proposal")
    assert resp_none.status_code == 200, resp_none.text
    ids_none = [item["id"] for item in resp_none.json()["data"]]
    assert t1 not in ids_none


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_task(client):
    p_id = await create_test_patient(client)
    t_id = await create_task(client, p_id)
    resp = await client.delete(f"{BASE}/{t_id}")
    assert resp.status_code == 204

    resp2 = await client.get(f"{BASE}/{t_id}")
    assert resp2.status_code == 404


# ── Auth & Tenancy ───────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    p_id = await create_test_patient(client)
    t_id = await create_task(client, p_id)

    # Switch to different organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="other-org",
        permissions=TASK_PERMS,
    )

    resp = await client.get(f"{BASE}/{t_id}")
    assert resp.status_code == 404

    resp_patch = await client.patch(f"{BASE}/{t_id}", json={"status": "in-progress"})
    assert resp_patch.status_code == 404

    resp_del = await client.delete(f"{BASE}/{t_id}")
    assert resp_del.status_code == 404

    resp_list = await client.get(BASE + "/")
    assert resp_list.status_code == 200
    ids = [item["id"] for item in resp_list.json()["data"]]
    assert t_id not in ids


async def test_orgless_token_rejected_403(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=TASK_PERMS,
    )
    resp = await client.post(BASE + "/", json=minimal_task(10001))
    assert resp.status_code == 403

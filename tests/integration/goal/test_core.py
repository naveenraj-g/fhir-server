"""Core Goal endpoint coverage.

Goal has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_goal,
    assert_paginated,
    assert_plain_goal,
)
from tests.integration.goal.support import (
    BASE,
    FHIR_ACCEPT,
    create_test_condition,
    create_test_organization,
    create_test_patient,
    create_test_practitioner,
    full_goal,
    minimal_goal,
)

GOAL_PERMS = [
    "goal:create",
    "goal:read",
    "goal:update",
    "goal:delete",
    "patient:create",
    "patient:read",
    "organization:create",
    "organization:read",
    "practitioner:create",
    "practitioner:read",
    "condition:create",
    "condition:read",
]


async def create_goal(client, patient_id: int) -> int:
    """Helper to create a minimal Goal and return public ID."""
    resp = await client.post(BASE + "/", json=minimal_goal(patient_id))
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_goal_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_goal(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_goal(data)
    assert data["subject"] == f"Patient/{p_id}"
    assert data["lifecycle_status"] == "active"
    assert data["description"]["text"] == "Follow-up dietary regime"
    assert data["id"] >= 460000


async def test_create_goal_full(client):
    p_id = await create_test_patient(client)
    pr_id = await create_test_practitioner(client)
    org_id = await create_test_organization(client)
    c_id = await create_test_condition(client, p_id)

    payload = full_goal(p_id, pr_id, org_id, c_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_goal(data)
    assert data["lifecycle_status"] == "active"
    assert data["subject"] == f"Patient/{p_id}"
    assert data["expressed_by"] == f"Practitioner/{pr_id}"
    assert len(data["category"]) == 1
    assert data["category"][0]["text"] == "Dietary"
    assert len(data["target"]) == 1
    assert data["target"][0]["measure_text"] == "Weight"
    assert data["target"][0]["detail_quantity_value"] == 70.0
    assert len(data["addresses"]) == 1
    assert data["addresses"][0]["reference"] == f"Condition/{c_id}"
    assert len(data["note"]) == 1
    assert data["note"][0]["text"] == "Patient motivated to follow diet plan."
    assert len(data["outcome_code"]) == 1
    assert data["outcome_code"][0]["text"] == "Normal weight achieved"
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "GOAL-123"


async def test_create_goal_fhir(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/", json=minimal_goal(p_id), headers=FHIR_ACCEPT
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_goal(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["lifecycleStatus"] == "active"
    assert data["description"]["text"] == "Follow-up dietary regime"


async def test_create_goal_invalid_subject_fails(client):
    resp = await client.post(
        BASE + "/",
        json={
            "lifecycle_status": "active",
            "description_text": "Exercise regularly",
            "subject": "Patient/999999",
        },
    )
    assert resp.status_code == 422, resp.text


async def test_create_goal_missing_required(client):
    p_id = await create_test_patient(client)
    # Missing description
    resp = await client.post(
        BASE + "/",
        json={
            "lifecycle_status": "active",
            "subject": f"Patient/{p_id}",
        },
    )
    assert resp.status_code == 422, resp.text


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_goal_plain(client):
    p_id = await create_test_patient(client)
    g_id = await create_goal(client, p_id)
    resp = await client.get(f"{BASE}/{g_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_goal(data, id=g_id)
    assert data["lifecycle_status"] == "active"


async def test_get_goal_fhir(client):
    p_id = await create_test_patient(client)
    g_id = await create_goal(client, p_id)
    resp = await client.get(f"{BASE}/{g_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_goal(data, id=str(g_id))
    assert data["lifecycleStatus"] == "active"


async def test_get_goal_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert resp.status_code == 404, resp.text


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_goal_fields(client):
    p_id = await create_test_patient(client)
    g_id = await create_goal(client, p_id)

    resp = await client.patch(
        f"{BASE}/{g_id}",
        json={
            "lifecycle_status": "completed",
            "priority_text": "low-priority",
            "status_reason": "Goal fully achieved",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["lifecycle_status"] == "completed"
    assert data["priority"]["text"] == "low-priority"
    assert data["status_reason"] == "Goal fully achieved"


async def test_patch_goal_sub_lists_replace(client):
    p_id = await create_test_patient(client)
    g_id = await create_goal(client, p_id)

    # Patch with new target and new note
    resp = await client.patch(
        f"{BASE}/{g_id}",
        json={
            "target": [
                {
                    "measure_text": "BMI",
                    "detail_quantity_value": 22.5,
                    "detail_quantity_unit": "kg/m2",
                }
            ],
            "note": ["Updated note on progress."],
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["target"]) == 1
    assert data["target"][0]["measure_text"] == "BMI"
    assert data["target"][0]["detail_quantity_value"] == 22.5
    assert len(data["note"]) == 1
    assert data["note"][0]["text"] == "Updated note on progress."


async def test_patch_goal_not_found(client):
    resp = await client.patch(
        f"{BASE}/999999",
        json={"lifecycle_status": "completed"},
    )
    assert resp.status_code == 404, resp.text


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_goals_plain(client):
    p_id = await create_test_patient(client)
    await create_goal(client, p_id)

    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    assert any(g["subject"] == f"Patient/{p_id}" for g in data["data"])


async def test_list_goals_fhir(client):
    p_id = await create_test_patient(client)
    await create_goal(client, p_id)

    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)


async def test_list_goals_filter_subject(client):
    p1 = await create_test_patient(client)
    p2 = await create_test_patient(client)
    await create_goal(client, p1)
    await create_goal(client, p2)

    resp = await client.get(BASE + f"/?subject=Patient/{p1}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["subject"] == f"Patient/{p1}"


async def test_list_goals_filter_lifecycle_status(client):
    p_id = await create_test_patient(client)
    g_id = await create_goal(client, p_id)

    await client.patch(f"{BASE}/{g_id}", json={"lifecycle_status": "completed"})

    resp = await client.get(BASE + "/?lifecycle-status=completed")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert any(g["id"] == g_id for g in data["data"])

    resp_active = await client.get(BASE + "/?lifecycle-status=active")
    assert resp_active.status_code == 200, resp_active.text
    data_active = resp_active.json()
    assert not any(g["id"] == g_id for g in data_active["data"])


async def test_list_goals_pagination(client):
    p_id = await create_test_patient(client)
    await create_goal(client, p_id)
    await create_goal(client, p_id)

    resp = await client.get(BASE + f"/?subject=Patient/{p_id}&limit=1&offset=0")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["limit"] == 1
    assert len(data["data"]) == 1
    assert data["total"] >= 2


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_goal(client):
    p_id = await create_test_patient(client)
    g_id = await create_goal(client, p_id)

    resp = await client.delete(f"{BASE}/{g_id}")
    assert resp.status_code == 204, resp.text

    get_resp = await client.get(f"{BASE}/{g_id}")
    assert get_resp.status_code == 404, get_resp.text


async def test_delete_goal_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert resp.status_code == 404, resp.text


# ── Auth & Isolation ─────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    p_id = await create_test_patient(client)
    g_id = await create_goal(client, p_id)

    # Switch to different organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-other",
        permissions=GOAL_PERMS,
    )

    get_resp = await client.get(f"{BASE}/{g_id}")
    assert get_resp.status_code == 404, get_resp.text

    patch_resp = await client.patch(
        f"{BASE}/{g_id}", json={"lifecycle_status": "completed"}
    )
    assert patch_resp.status_code == 404, patch_resp.text

    del_resp = await client.delete(f"{BASE}/{g_id}")
    assert del_resp.status_code == 404, del_resp.text


async def test_org_less_actor_rejected(client):
    p_id = await create_test_patient(client)

    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=GOAL_PERMS,
    )

    resp = await client.post(BASE + "/", json=minimal_goal(p_id))
    assert resp.status_code == 403, resp.text

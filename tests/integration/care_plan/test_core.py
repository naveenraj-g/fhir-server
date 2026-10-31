"""Core care_plan endpoint coverage.

CarePlan has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_care_plan,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_care_plan,
)
from tests.integration.care_plan.support import (
    BASE,
    FHIR_ACCEPT,
    create_care_plan,
    create_test_condition,
    create_test_patient,
    create_test_practitioner,
    full_care_plan,
    minimal_care_plan,
)

CARE_PLAN_PERMS = [
    "care_plan:create",
    "care_plan:read",
    "care_plan:update",
    "care_plan:delete",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "condition:create",
    "condition:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_care_plan_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_care_plan(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_care_plan(data)
    assert data["subject"] == f"Patient/{p_id}"
    assert data["status"] == "active"
    assert data["intent"] == "plan"


async def test_create_care_plan_full(client):
    p_id = await create_test_patient(client)
    pr_id = await create_test_practitioner(client)
    c_id = await create_test_condition(client, p_id)
    payload = full_care_plan(p_id, pr_id, c_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_care_plan(data)
    assert data["status"] == "active"
    assert data["intent"] == "plan"
    assert data["title"] == "Diabetes Care Plan"
    assert len(data["categories"]) == 1
    assert data["categories"][0]["text"] == "Diabetes self management plan"
    assert data["author"] == f"Practitioner/{pr_id}"
    assert data["author_display"] == "Dr. Adam Careful"
    assert len(data["addresses"]) == 1
    assert data["addresses"][0]["reference"] == f"Condition/{c_id}"
    assert len(data["activities"]) == 1
    assert data["activities"][0]["detail"]["kind"] == "CommunicationRequest"
    assert len(data["notes"]) == 1
    assert data["notes"][0]["text"] == "Initial plan established following diagnosis."


async def test_create_care_plan_fhir_content_negotiation(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/",
        json=minimal_care_plan(p_id),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_care_plan(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "active"
    assert data["intent"] == "plan"


async def test_create_care_plan_validation_failure(client):
    # Missing required 'intent'
    resp = await client.post(
        BASE + "/",
        json={"status": "active", "subject": "Patient/10001"},
    )
    assert resp.status_code == 422


async def test_create_care_plan_nonexistent_subject(client):
    # Reference to non-existent Patient
    resp = await client.post(
        BASE + "/",
        json={"status": "active", "intent": "plan", "subject": "Patient/9999999"},
    )
    assert resp.status_code == 422


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_care_plan_plain(client):
    cp = await create_care_plan(client)
    resp = await client.get(f"{BASE}/{cp['id']}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_care_plan(data)
    assert data["id"] == cp["id"]


async def test_get_care_plan_fhir(client):
    cp = await create_care_plan(client)
    resp = await client.get(f"{BASE}/{cp['id']}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_care_plan(data)
    assert data["id"] == str(cp["id"])


async def test_get_care_plan_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_care_plan_scalar_fields(client):
    cp = await create_care_plan(client, title="Original Title")
    patch_body = {"title": "Updated Title", "status": "completed"}
    resp = await client.patch(f"{BASE}/{cp['id']}", json=patch_body)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["title"] == "Updated Title"
    assert data["status"] == "completed"


async def test_patch_care_plan_replace_sub_resources(client):
    cp = await create_care_plan(
        client,
        category=[
            {"text": "Initial Category"}
        ],
    )
    assert len(cp["categories"]) == 1

    # Replace category with a new one
    patch_body = {
        "category": [
            {"text": "Replacement Category 1"},
            {"text": "Replacement Category 2"},
        ]
    }
    resp = await client.patch(f"{BASE}/{cp['id']}", json=patch_body)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["categories"]) == 2
    cat_texts = {c["text"] for c in data["categories"]}
    assert cat_texts == {"Replacement Category 1", "Replacement Category 2"}


async def test_patch_care_plan_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"title": "Test"})
    assert resp.status_code == 404


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_care_plans_plain(client):
    await create_care_plan(client)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    assert len(data["data"]) >= 1
    assert_plain_care_plan(data["data"][0])


async def test_list_care_plans_fhir_bundle(client):
    await create_care_plan(client)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    assert len(data.get("entry", [])) >= 1


async def test_list_care_plans_filters(client):
    p_id = await create_test_patient(client)
    cp1 = await create_care_plan(
        client,
        patient_id=p_id,
        title="Hypertension Plan",
        status="active",
        intent="plan",
    )
    cp2 = await create_care_plan(
        client,
        patient_id=p_id,
        title="Asthma Plan",
        status="completed",
        intent="proposal",
    )

    # Filter by title
    resp = await client.get(BASE + "/?title=Hypertension")
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()["data"]]
    assert cp1["id"] in ids
    assert cp2["id"] not in ids

    # Filter by status
    resp = await client.get(BASE + "/?status=completed")
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()["data"]]
    assert cp2["id"] in ids

    # Filter by subject
    resp = await client.get(f"{BASE}/?subject=Patient/{p_id}")
    assert resp.status_code == 200
    ids = [d["id"] for d in resp.json()["data"]]
    assert cp1["id"] in ids
    assert cp2["id"] in ids


async def test_list_care_plans_pagination(client):
    p_id = await create_test_patient(client)
    for i in range(3):
        await create_care_plan(client, patient_id=p_id, title=f"Paginated Plan {i}")

    resp = await client.get(f"{BASE}/?subject=Patient/{p_id}&limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["data"]) == 2
    assert data["total"] >= 3


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_care_plan_success(client):
    cp = await create_care_plan(client)
    resp = await client.delete(f"{BASE}/{cp['id']}")
    assert resp.status_code == 204

    # Confirm it's gone
    resp_get = await client.get(f"{BASE}/{cp['id']}")
    assert resp_get.status_code == 404


async def test_delete_care_plan_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert resp.status_code == 404


# ── Auth / Multi-Tenancy ─────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    cp = await create_care_plan(client)

    # Switch client to a different organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-other",
        permissions=CARE_PLAN_PERMS,
    )
    # Must return 404 (never 403) so existence is not leaked across tenants
    resp = await client.get(f"{BASE}/{cp['id']}")
    assert resp.status_code == 404

    resp_patch = await client.patch(f"{BASE}/{cp['id']}", json={"title": "Hacked"})
    assert resp_patch.status_code == 404

    resp_del = await client.delete(f"{BASE}/{cp['id']}")
    assert resp_del.status_code == 404


async def test_org_less_token_rejected(client):
    p_id = await create_test_patient(client)

    # Token with no activeOrganizationId
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=CARE_PLAN_PERMS,
    )
    resp = await client.post(BASE + "/", json=minimal_care_plan(p_id))
    assert resp.status_code == 403


async def test_insufficient_permissions(client):
    p_id = await create_test_patient(client)

    # User with read-only permissions
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=["care_plan:read"]
    )
    resp = await client.post(BASE + "/", json=minimal_care_plan(p_id))
    assert resp.status_code == 403

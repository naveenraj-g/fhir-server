"""Core care_team endpoint coverage.

CareTeam has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_care_team,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_care_team,
)
from tests.integration.care_team.support import (
    BASE,
    FHIR_ACCEPT,
    create_care_team,
    create_test_condition,
    create_test_organization,
    create_test_patient,
    create_test_practitioner,
    full_care_team,
    minimal_care_team,
)

CARE_TEAM_PERMS = [
    "care_team:create",
    "care_team:read",
    "care_team:update",
    "care_team:delete",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "organization:create",
    "organization:read",
    "condition:create",
    "condition:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_care_team_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_care_team(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_care_team(data)
    assert data["subject"] == f"Patient/{p_id}"
    assert data["status"] == "active"
    assert data["name"] == "Minimal Care Team"


async def test_create_care_team_full(client):
    p_id = await create_test_patient(client)
    pr_id = await create_test_practitioner(client)
    org_id = await create_test_organization(client)
    c_id = await create_test_condition(client, p_id)
    payload = full_care_team(p_id, pr_id, org_id, c_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_care_team(data)
    assert data["status"] == "active"
    assert data["name"] == "Comprehensive Cardiology Care Team"
    assert len(data["categories"]) == 1
    assert data["categories"][0]["text"] == "Longitudinal care-coordination"
    assert len(data["participants"]) == 1
    p = data["participants"][0]
    assert p["member"] == f"Practitioner/{pr_id}"
    assert p["member_display"] == "Dr. Adam Careful"
    assert p["on_behalf_of"] == f"Organization/{org_id}"
    assert len(p["roles"]) == 1
    assert p["roles"][0]["text"] == "Lead Cardiologist"
    assert len(data["managing_organizations"]) == 1
    assert data["managing_organizations"][0]["reference"] == f"Organization/{org_id}"
    assert len(data["reason_references"]) == 1
    assert data["reason_references"][0]["reference"] == f"Condition/{c_id}"
    assert len(data["telecoms"]) == 1
    assert data["telecoms"][0]["value"] == "+1-555-555-5555"
    assert len(data["notes"]) == 1
    assert data["notes"][0]["text"] == "Initial care team established following diagnosis."


async def test_create_care_team_fhir_content_negotiation(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/",
        json=minimal_care_team(p_id),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_care_team(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "active"
    assert data["name"] == "Minimal Care Team"


async def test_create_care_team_validation_failure(client):
    # Invalid status value
    resp = await client.post(
        BASE + "/",
        json={"status": "invalid-status", "subject": "Patient/99999"},
    )
    assert resp.status_code == 422, resp.text


async def test_create_care_team_rejects_missing_patient(client):
    resp = await client.post(
        BASE + "/",
        json={"status": "active", "subject": "Patient/999999"},
    )
    assert resp.status_code == 422, resp.text


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_care_team_plain(client):
    ct = await create_care_team(client)
    resp = await client.get(f"{BASE}/{ct['id']}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_care_team(data, id=ct["id"])
    assert data["name"] == ct["name"]


async def test_get_care_team_fhir(client):
    ct = await create_care_team(client)
    resp = await client.get(f"{BASE}/{ct['id']}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_care_team(data, id=str(ct["id"]))


async def test_get_care_team_not_found(client):
    resp = await client.get(f"{BASE}/99999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, 404)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_care_team_scalar_fields(client):
    ct = await create_care_team(client)
    patch_body = {
        "name": "Updated Care Team Name",
        "status": "suspended",
    }
    resp = await client.patch(f"{BASE}/{ct['id']}", json=patch_body)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_care_team(data, id=ct["id"])
    assert data["name"] == "Updated Care Team Name"
    assert data["status"] == "suspended"


async def test_patch_care_team_sub_resources_replace(client):
    ct = await create_care_team(client)
    patch_body = {
        "telecom": [
            {
                "system": "email",
                "value": "team@example.com",
                "use": "work",
            }
        ],
        "note": [{"text": "Updated note on care team."}],
    }
    resp = await client.patch(f"{BASE}/{ct['id']}", json=patch_body)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["telecoms"]) == 1
    assert data["telecoms"][0]["system"] == "email"
    assert data["telecoms"][0]["value"] == "team@example.com"
    assert len(data["notes"]) == 1
    assert data["notes"][0]["text"] == "Updated note on care team."


async def test_patch_care_team_not_found(client):
    resp = await client.patch(f"{BASE}/99999999", json={"name": "Ghost Care Team"})
    assert resp.status_code == 404, resp.text


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_care_teams_plain(client):
    ct = await create_care_team(client)
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    ids = [item["id"] for item in data["data"]]
    assert ct["id"] in ids


async def test_list_care_teams_fhir_bundle(client):
    ct = await create_care_team(client)
    resp = await client.get(f"{BASE}/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    entry_ids = [e["resource"]["id"] for e in data["entry"]]
    assert str(ct["id"]) in entry_ids


async def test_list_care_teams_filters(client):
    p_id = await create_test_patient(client)
    ct = await create_care_team(client, patient_id=p_id, name="Unique Filter Name 123")

    # Filter by name
    resp = await client.get(f"{BASE}/?name=Filter Name 123")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert len(items) >= 1
    assert any(x["id"] == ct["id"] for x in items)

    # Filter by subject
    resp = await client.get(f"{BASE}/?subject=Patient/{p_id}")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert any(x["id"] == ct["id"] for x in items)

    # Filter by status
    resp = await client.get(f"{BASE}/?status=active")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert any(x["id"] == ct["id"] for x in items)


async def test_list_care_teams_pagination(client):
    resp = await client.get(f"{BASE}/?limit=2&offset=0")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["data"]) <= 2


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_care_team_success(client):
    ct = await create_care_team(client)
    del_resp = await client.delete(f"{BASE}/{ct['id']}")
    assert del_resp.status_code == 204, del_resp.text

    get_resp = await client.get(f"{BASE}/{ct['id']}")
    assert get_resp.status_code == 404


async def test_delete_care_team_not_found(client):
    resp = await client.delete(f"{BASE}/99999999")
    assert resp.status_code == 404, resp.text


# ── Auth & Scoping ───────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    ct = await create_care_team(client)

    # Switch user to another organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-other",
        permissions=CARE_TEAM_PERMS,
    )
    # Get -> 404 (not 403, no leak)
    resp = await client.get(f"{BASE}/{ct['id']}")
    assert resp.status_code == 404, resp.text

    # Patch -> 404
    resp = await client.patch(f"{BASE}/{ct['id']}", json={"name": "Hacked"})
    assert resp.status_code == 404, resp.text

    # Delete -> 404
    resp = await client.delete(f"{BASE}/{ct['id']}")
    assert resp.status_code == 404, resp.text

    # List -> does not include ct["id"]
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert ct["id"] not in ids


async def test_org_less_token_rejected(client):
    p_id = await create_test_patient(client)

    # Actor without org_id
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=CARE_TEAM_PERMS,
    )
    resp = await client.post(BASE + "/", json=minimal_care_team(p_id))
    assert resp.status_code == 403, resp.text

    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 403, resp.text


async def test_missing_permission_rejected(client):
    p_id = await create_test_patient(client)

    # No care_team permissions
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=["patient:read"]
    )
    resp = await client.post(BASE + "/", json=minimal_care_team(p_id))
    assert resp.status_code == 403, resp.text

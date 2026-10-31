"""Core episode_of_care endpoint coverage.

EpisodeOfCare has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_episode_of_care,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_episode_of_care,
)
from tests.integration.episode_of_care.support import (
    BASE,
    FHIR_ACCEPT,
    create_episode_of_care,
    create_test_care_team,
    create_test_condition,
    create_test_organization,
    create_test_patient,
    create_test_practitioner,
    full_episode_of_care,
    minimal_episode_of_care,
)

EPISODE_OF_CARE_PERMS = [
    "episode_of_care:create",
    "episode_of_care:read",
    "episode_of_care:update",
    "episode_of_care:delete",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "organization:create",
    "organization:read",
    "condition:create",
    "condition:read",
    "care_team:create",
    "care_team:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_episode_of_care_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_episode_of_care(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_episode_of_care(data)
    assert data["patient"] == f"Patient/{p_id}"
    assert data["status"] == "active"


async def test_create_episode_of_care_full(client):
    p_id = await create_test_patient(client)
    pr_id = await create_test_practitioner(client)
    org_id = await create_test_organization(client)
    c_id = await create_test_condition(client, p_id)
    ct_id = await create_test_care_team(client, p_id)
    payload = full_episode_of_care(p_id, pr_id, org_id, c_id, ct_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_episode_of_care(data)
    assert data["status"] == "active"
    assert data["patient"] == f"Patient/{p_id}"
    assert data["managing_organization"] == f"Organization/{org_id}"
    assert data["care_manager"] == f"Practitioner/{pr_id}"
    assert len(data["status_history"]) == 1
    assert data["status_history"][0]["status"] == "planned"
    assert len(data["types"]) == 1
    assert data["types"][0]["text"] == "Home and Community Care"
    assert len(data["diagnoses"]) == 1
    assert data["diagnoses"][0]["condition"] == f"Condition/{c_id}"
    assert data["diagnoses"][0]["rank"] == 1
    assert len(data["teams"]) == 1
    assert data["teams"][0]["reference"] == f"CareTeam/{ct_id}"
    assert len(data["identifiers"]) == 1
    assert data["identifiers"][0]["value"] == "EOC-12345"


async def test_create_episode_of_care_fhir_content_negotiation(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/",
        json=minimal_episode_of_care(p_id),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_episode_of_care(data)
    assert data["patient"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "active"


async def test_create_episode_of_care_validation_failure(client):
    # Invalid status value
    resp = await client.post(
        BASE + "/",
        json={"status": "invalid-status", "patient": "Patient/99999"},
    )
    assert resp.status_code == 422, resp.text


async def test_create_episode_of_care_rejects_missing_patient(client):
    resp = await client.post(
        BASE + "/",
        json={"status": "active", "patient": "Patient/999999"},
    )
    assert resp.status_code == 422, resp.text


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_episode_of_care_plain(client):
    eoc = await create_episode_of_care(client)
    resp = await client.get(f"{BASE}/{eoc['id']}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_episode_of_care(data, id=eoc["id"])
    assert data["status"] == eoc["status"]


async def test_get_episode_of_care_fhir(client):
    eoc = await create_episode_of_care(client)
    resp = await client.get(f"{BASE}/{eoc['id']}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_episode_of_care(data, id=str(eoc["id"]))


async def test_get_episode_of_care_not_found(client):
    resp = await client.get(f"{BASE}/99999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, 404)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_episode_of_care_scalar_fields(client):
    eoc = await create_episode_of_care(client)
    patch_body = {
        "status": "onhold",
    }
    resp = await client.patch(f"{BASE}/{eoc['id']}", json=patch_body)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_episode_of_care(data, id=eoc["id"])
    assert data["status"] == "onhold"


async def test_patch_episode_of_care_sub_resources_replace(client):
    eoc = await create_episode_of_care(client)
    patch_body = {
        "status_history": [
            {
                "status": "active",
                "period_start": "2026-02-01T00:00:00Z",
            }
        ],
        "identifier": [
            {
                "use": "secondary",
                "system": "http://example.org/internal",
                "value": "INT-999",
            }
        ],
    }
    resp = await client.patch(f"{BASE}/{eoc['id']}", json=patch_body)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["status_history"]) == 1
    assert data["status_history"][0]["status"] == "active"
    assert len(data["identifiers"]) == 1
    assert data["identifiers"][0]["value"] == "INT-999"


async def test_patch_episode_of_care_not_found(client):
    resp = await client.patch(f"{BASE}/99999999", json={"status": "finished"})
    assert resp.status_code == 404, resp.text


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_episodes_of_care_plain(client):
    eoc = await create_episode_of_care(client)
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    ids = [item["id"] for item in data["data"]]
    assert eoc["id"] in ids


async def test_list_episodes_of_care_fhir_bundle(client):
    eoc = await create_episode_of_care(client)
    resp = await client.get(f"{BASE}/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    entry_ids = [e["resource"]["id"] for e in data["entry"]]
    assert str(eoc["id"]) in entry_ids


async def test_list_episodes_of_care_filters(client):
    p_id = await create_test_patient(client)
    eoc = await create_episode_of_care(
        client,
        patient_id=p_id,
        identifier=[{"system": "http://test.org/id", "value": "FILTER-ID-123"}],
    )

    # Filter by patient
    resp = await client.get(f"{BASE}/?patient=Patient/{p_id}")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert len(items) >= 1
    assert any(x["id"] == eoc["id"] for x in items)

    # Filter by identifier
    resp = await client.get(f"{BASE}/?identifier=FILTER-ID-123")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert any(x["id"] == eoc["id"] for x in items)

    # Filter by status
    resp = await client.get(f"{BASE}/?status=active")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert any(x["id"] == eoc["id"] for x in items)


async def test_list_episodes_of_care_pagination(client):
    resp = await client.get(f"{BASE}/?limit=2&offset=0")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["data"]) <= 2


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_episode_of_care_success(client):
    eoc = await create_episode_of_care(client)
    del_resp = await client.delete(f"{BASE}/{eoc['id']}")
    assert del_resp.status_code == 204, del_resp.text

    get_resp = await client.get(f"{BASE}/{eoc['id']}")
    assert get_resp.status_code == 404


async def test_delete_episode_of_care_not_found(client):
    resp = await client.delete(f"{BASE}/99999999")
    assert resp.status_code == 404, resp.text


# ── Auth & Scoping ───────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    eoc = await create_episode_of_care(client)

    # Switch user to another organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-other",
        permissions=EPISODE_OF_CARE_PERMS,
    )
    # Get -> 404 (not 403, no leak)
    resp = await client.get(f"{BASE}/{eoc['id']}")
    assert resp.status_code == 404, resp.text

    # Patch -> 404
    resp = await client.patch(f"{BASE}/{eoc['id']}", json={"status": "cancelled"})
    assert resp.status_code == 404, resp.text

    # Delete -> 404
    resp = await client.delete(f"{BASE}/{eoc['id']}")
    assert resp.status_code == 404, resp.text

    # List -> does not include eoc["id"]
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert eoc["id"] not in ids


async def test_org_less_token_rejected(client):
    p_id = await create_test_patient(client)

    # Actor without org_id
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=EPISODE_OF_CARE_PERMS,
    )
    resp = await client.post(BASE + "/", json=minimal_episode_of_care(p_id))
    assert resp.status_code == 403, resp.text

    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 403, resp.text


async def test_missing_permission_rejected(client):
    p_id = await create_test_patient(client)

    # No episode_of_care permissions
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=["patient:read"]
    )
    resp = await client.post(BASE + "/", json=minimal_episode_of_care(p_id))
    assert resp.status_code == 403, resp.text

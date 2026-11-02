"""Core DetectedIssue endpoint coverage.

DetectedIssue has 5 endpoints (create/get/patch/list/delete),
no sub-resource routes and no /me route.

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
    assert_fhir_detected_issue,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_detected_issue,
)
from tests.integration.detected_issue.support import (
    BASE,
    FHIR_ACCEPT,
    create_detected_issue,
    create_test_condition,
    create_test_observation,
    create_test_organization,
    create_test_patient,
    create_test_practitioner,
    full_detected_issue,
    minimal_detected_issue,
)

DETECTED_ISSUE_PERMS = [
    "detected_issue:create",
    "detected_issue:read",
    "detected_issue:update",
    "detected_issue:delete",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "condition:create",
    "condition:read",
    "observation:create",
    "observation:read",
    "organization:create",
    "organization:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_detected_issue_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_detected_issue(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_detected_issue(data)
    assert data["patient"]["reference"] == f"Patient/{p_id}"
    assert data["id"] >= 540000
    assert data["status"] == "final"


async def test_create_detected_issue_full(client):
    p_id = await create_test_patient(client)
    pract_id = await create_test_practitioner(client)
    cond_id = await create_test_condition(client, p_id)
    obs_id = await create_test_observation(client, p_id)
    org_id = await create_test_organization(client)

    payload = full_detected_issue(
        p_id,
        practitioner_id=pract_id,
        condition_id=cond_id,
        observation_id=obs_id,
        organization_id=org_id,
    )
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_detected_issue(data)
    assert data["patient"]["reference"] == f"Patient/{p_id}"
    assert data["author"]["reference"] == f"Practitioner/{pract_id}"
    assert data["severity"] == "high"
    assert len(data["implicated"]) == 1
    assert data["implicated"][0]["reference"] == f"Condition/{cond_id}"
    assert len(data["evidence"]) == 1
    assert data["evidence"][0]["detail"][0]["reference"] == f"Observation/{obs_id}"
    assert len(data["mitigation"]) == 1
    assert data["mitigation"][0]["author"]["reference"] == f"Practitioner/{pract_id}"
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["assigner_reference"] == f"Organization/{org_id}"


async def test_create_detected_issue_fhir_content_negotiation(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/",
        json=minimal_detected_issue(p_id),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_detected_issue(data)
    assert data["resourceType"] == "DetectedIssue"
    assert data["patient"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "final"


async def test_create_detected_issue_invalid_reference(client):
    payload = {
        "status": "final",
        "patient": {"reference": "Patient/999999999"},
    }
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text
    assert_operation_outcome(resp.json(), 422, resp.status_code)


# ── Read ─────────────────────────────────────────────────────────────────


async def test_read_detected_issue_plain(client):
    p_id = await create_test_patient(client)
    issue_id = await create_detected_issue(client, p_id)
    resp = await client.get(f"{BASE}/{issue_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_detected_issue(data)
    assert data["id"] == issue_id
    assert data["patient"]["reference"] == f"Patient/{p_id}"


async def test_read_detected_issue_fhir(client):
    p_id = await create_test_patient(client)
    issue_id = await create_detected_issue(client, p_id)
    resp = await client.get(f"{BASE}/{issue_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_detected_issue(data)
    assert data["id"] == str(issue_id)
    assert data["patient"]["reference"] == f"Patient/{p_id}"


async def test_read_detected_issue_not_found(client):
    resp = await client.get(f"{BASE}/999999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_detected_issue_scalars(client):
    p_id = await create_test_patient(client)
    issue_id = await create_detected_issue(client, p_id)

    patch_payload = {
        "severity": "moderate",
        "detail": "Updated severity after consultation.",
    }
    resp = await client.patch(f"{BASE}/{issue_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["severity"] == "moderate"
    assert data["detail"] == "Updated severity after consultation."
    assert data["patient"]["reference"] == f"Patient/{p_id}"


async def test_patch_detected_issue_replace_sub_lists(client):
    p_id = await create_test_patient(client)
    issue_id = await create_detected_issue(client, p_id)

    # Replace mitigation and implicated
    cond_id = await create_test_condition(client, p_id)
    patch_payload = {
        "implicated": [
            {
                "reference": f"Condition/{cond_id}",
                "reference_display": "Updated implicated condition",
            }
        ],
        "mitigation": [
            {
                "action": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                            "code": "13",
                            "display": "Consulted Prescriber",
                        }
                    ],
                    "text": "Discontinued problematic medication",
                },
                "date": "2026-02-02T09:00:00Z",
            }
        ],
    }
    resp = await client.patch(f"{BASE}/{issue_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["implicated"]) == 1
    assert data["implicated"][0]["reference"] == f"Condition/{cond_id}"
    assert len(data["mitigation"]) == 1
    assert data["mitigation"][0]["action"]["text"] == "Discontinued problematic medication"


async def test_patch_detected_issue_not_found(client):
    resp = await client.patch(f"{BASE}/999999999", json={"status": "cancelled"})
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_detected_issues_plain(client):
    p_id = await create_test_patient(client)
    await create_detected_issue(client, p_id)
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    assert data["total"] >= 1
    assert len(data["data"]) >= 1
    assert_plain_detected_issue(data["data"][0])


async def test_list_detected_issues_fhir_bundle(client):
    p_id = await create_test_patient(client)
    await create_detected_issue(client, p_id)
    resp = await client.get(f"{BASE}/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    assert data["total"] >= 1
    assert len(data["entry"]) >= 1
    assert_fhir_detected_issue(data["entry"][0]["resource"])


async def test_list_detected_issues_filters(client):
    p1 = await create_test_patient(client)
    p2 = await create_test_patient(client)

    await client.post(BASE + "/", json={"status": "preliminary", "patient": {"reference": f"Patient/{p1}"}})
    await client.post(BASE + "/", json={"status": "final", "patient": {"reference": f"Patient/{p2}"}})

    # Filter by status
    resp = await client.get(f"{BASE}/?status=preliminary")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert all(item["status"] == "preliminary" for item in items)

    # Filter by patient
    resp = await client.get(f"{BASE}/?patient=Patient/{p2}")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert len(items) >= 1
    assert all(item["patient"]["reference"] == f"Patient/{p2}" for item in items)


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_detected_issue(client):
    p_id = await create_test_patient(client)
    cond_id = await create_test_condition(client, p_id)
    obs_id = await create_test_observation(client, p_id)
    pract_id = await create_test_practitioner(client)

    payload = full_detected_issue(
        p_id,
        practitioner_id=pract_id,
        condition_id=cond_id,
        observation_id=obs_id,
    )
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    issue_id = resp.json()["id"]

    del_resp = await client.delete(f"{BASE}/{issue_id}")
    assert del_resp.status_code == 204, del_resp.text

    get_resp = await client.get(f"{BASE}/{issue_id}")
    assert get_resp.status_code == 404


async def test_delete_detected_issue_not_found(client):
    resp = await client.delete(f"{BASE}/999999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Multi-Tenancy & Auth ────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    p_id = await create_test_patient(client)
    issue_id = await create_detected_issue(client, p_id)

    # Switch to different organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-other",
        permissions=DETECTED_ISSUE_PERMS,
    )

    # Read should return 404
    get_resp = await client.get(f"{BASE}/{issue_id}")
    assert get_resp.status_code == 404

    # Patch should return 404
    patch_resp = await client.patch(f"{BASE}/{issue_id}", json={"status": "cancelled"})
    assert patch_resp.status_code == 404

    # Delete should return 404
    del_resp = await client.delete(f"{BASE}/{issue_id}")
    assert del_resp.status_code == 404


async def test_org_less_token_rejected(client):
    # Org-less user
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=DETECTED_ISSUE_PERMS,
    )

    resp = await client.post(BASE + "/", json={"status": "final"})
    assert resp.status_code == 403

    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 403

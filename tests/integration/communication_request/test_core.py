"""Core CommunicationRequest endpoint coverage.

CommunicationRequest has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_communication_request,
    assert_paginated,
    assert_plain_communication_request,
)
from tests.integration.communication_request.support import (
    BASE,
    FHIR_ACCEPT,
    create_test_condition,
    create_test_encounter,
    create_test_observation,
    create_test_organization,
    create_test_patient,
    create_test_practitioner,
    full_communication_request,
    minimal_communication_request,
)

COMM_PERMS = [
    "communication_request:create",
    "communication_request:read",
    "communication_request:update",
    "communication_request:delete",
    "patient:create",
    "patient:read",
    "organization:create",
    "organization:read",
    "practitioner:create",
    "practitioner:read",
    "encounter:create",
    "encounter:read",
    "condition:create",
    "condition:read",
    "observation:create",
    "observation:read",
]


async def create_comm_req(client, patient_id: int) -> int:
    """Helper to create a minimal CommunicationRequest and return public ID."""
    resp = await client.post(BASE + "/", json=minimal_communication_request(patient_id))
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_communication_request_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_communication_request(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_communication_request(data)
    assert data["subject"] == f"Patient/{p_id}"
    assert data["status"] == "active"
    assert data["id"] >= 470000


async def test_create_communication_request_full(client):
    p_id = await create_test_patient(client)
    pr_id = await create_test_practitioner(client)
    org_id = await create_test_organization(client)
    enc_id = await create_test_encounter(client, p_id)
    c_id = await create_test_condition(client, p_id)

    payload = full_communication_request(
        p_id, pr_id, org_id, enc_id, c_id
    )
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_communication_request(data)
    assert data["status"] == "active"
    assert data["priority"] == "routine"
    assert data["do_not_perform"] is False
    assert data["subject"] == f"Patient/{p_id}"
    assert data["encounter"] == f"Encounter/{enc_id}"
    assert data["requester"] == f"Practitioner/{pr_id}"
    assert data["sender"] == f"Practitioner/{pr_id}"
    assert len(data["category"]) == 1
    assert data["category"][0]["text"] == "Notification"
    assert len(data["medium"]) == 1
    assert data["medium"][0]["text"] == "written"
    assert len(data["about"]) == 1
    assert data["about"][0]["reference"] == f"Condition/{c_id}"
    assert len(data["payload"]) == 2
    assert data["payload"][0]["content_string"] == "Please follow up on heart rate test results."
    assert data["payload"][1]["content_attachment"]["title"] == "Notes attachment"
    assert len(data["recipient"]) == 1
    assert data["recipient"][0]["reference"] == f"Patient/{p_id}"
    assert len(data["reason_code"]) == 1
    assert data["reason_code"][0]["text"] == "Abnormal lab result"
    assert len(data["reason_reference"]) == 1
    assert data["reason_reference"][0]["reference"] == f"Condition/{c_id}"
    assert len(data["note"]) == 1
    assert data["note"][0]["text"] == "Contacted patient by phone; left voicemail."
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "CR-12345"
    assert data["group_identifier_value"] == "GRP-12345"


async def test_create_communication_request_fhir(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/", json=minimal_communication_request(p_id), headers=FHIR_ACCEPT
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_communication_request(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "active"


async def test_create_communication_request_invalid_subject_fails(client):
    resp = await client.post(
        BASE + "/",
        json={
            "status": "active",
            "subject": "Patient/999999",
        },
    )
    assert resp.status_code == 422, resp.text


async def test_create_communication_request_missing_required(client):
    p_id = await create_test_patient(client)
    # Missing status
    resp = await client.post(
        BASE + "/",
        json={
            "subject": f"Patient/{p_id}",
        },
    )
    assert resp.status_code == 422, resp.text


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_communication_request_plain(client):
    p_id = await create_test_patient(client)
    cr_id = await create_comm_req(client, p_id)
    resp = await client.get(f"{BASE}/{cr_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_communication_request(data, id=cr_id)
    assert data["status"] == "active"


async def test_get_communication_request_fhir(client):
    p_id = await create_test_patient(client)
    cr_id = await create_comm_req(client, p_id)
    resp = await client.get(f"{BASE}/{cr_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_communication_request(data, id=str(cr_id))
    assert data["status"] == "active"


async def test_get_communication_request_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert resp.status_code == 404, resp.text


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_communication_request_fields(client):
    p_id = await create_test_patient(client)
    cr_id = await create_comm_req(client, p_id)

    resp = await client.patch(
        f"{BASE}/{cr_id}",
        json={
            "status": "completed",
            "priority": "urgent",
            "do_not_perform": True,
            "status_reason_text": "Request fulfilled by phone call",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "completed"
    assert data["priority"] == "urgent"
    assert data["do_not_perform"] is True
    assert data["status_reason_text"] == "Request fulfilled by phone call"


async def test_patch_communication_request_sub_lists_replace(client):
    p_id = await create_test_patient(client)
    cr_id = await create_comm_req(client, p_id)

    # Patch with new payload and new note
    resp = await client.patch(
        f"{BASE}/{cr_id}",
        json={
            "payload": [
                {
                    "content_string": "Updated payload message.",
                }
            ],
            "note": [
                {
                    "text": "Updated communication note.",
                }
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["payload"]) == 1
    assert data["payload"][0]["content_string"] == "Updated payload message."
    assert len(data["note"]) == 1
    assert data["note"][0]["text"] == "Updated communication note."


async def test_patch_communication_request_not_found(client):
    resp = await client.patch(
        f"{BASE}/999999",
        json={"status": "completed"},
    )
    assert resp.status_code == 404, resp.text


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_communication_requests_plain(client):
    p_id = await create_test_patient(client)
    await create_comm_req(client, p_id)

    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    assert any(c["subject"] == f"Patient/{p_id}" for c in data["data"])


async def test_list_communication_requests_fhir(client):
    p_id = await create_test_patient(client)
    await create_comm_req(client, p_id)

    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)


async def test_list_communication_requests_filter_subject(client):
    p1 = await create_test_patient(client)
    p2 = await create_test_patient(client)
    await create_comm_req(client, p1)
    await create_comm_req(client, p2)

    resp = await client.get(BASE + f"/?subject=Patient/{p1}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["subject"] == f"Patient/{p1}"


async def test_list_communication_requests_filter_status(client):
    p_id = await create_test_patient(client)
    cr_id = await create_comm_req(client, p_id)

    await client.patch(f"{BASE}/{cr_id}", json={"status": "completed"})

    resp = await client.get(BASE + "/?status=completed")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert any(c["id"] == cr_id for c in data["data"])

    resp_draft = await client.get(BASE + "/?status=draft")
    assert resp_draft.status_code == 200, resp_draft.text
    data_draft = resp_draft.json()
    assert not any(c["id"] == cr_id for c in data_draft["data"])


async def test_list_communication_requests_filter_priority(client):
    p_id = await create_test_patient(client)
    cr_id = await create_comm_req(client, p_id)

    await client.patch(f"{BASE}/{cr_id}", json={"priority": "urgent"})

    resp = await client.get(BASE + "/?priority=urgent")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert any(c["id"] == cr_id for c in data["data"])

    resp_asap = await client.get(BASE + "/?priority=asap")
    assert resp_asap.status_code == 200, resp_asap.text
    data_asap = resp_asap.json()
    assert not any(c["id"] == cr_id for c in data_asap["data"])


async def test_list_communication_requests_pagination(client):
    p_id = await create_test_patient(client)
    await create_comm_req(client, p_id)
    await create_comm_req(client, p_id)

    resp = await client.get(BASE + f"/?subject=Patient/{p_id}&limit=1&offset=0")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["limit"] == 1
    assert len(data["data"]) == 1
    assert data["total"] >= 2


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_communication_request(client):
    p_id = await create_test_patient(client)
    cr_id = await create_comm_req(client, p_id)

    resp = await client.delete(f"{BASE}/{cr_id}")
    assert resp.status_code == 204, resp.text

    get_resp = await client.get(f"{BASE}/{cr_id}")
    assert get_resp.status_code == 404, get_resp.text


async def test_delete_communication_request_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert resp.status_code == 404, resp.text


# ── Auth & Isolation ─────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    p_id = await create_test_patient(client)
    cr_id = await create_comm_req(client, p_id)

    # Switch to different organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-other",
        permissions=COMM_PERMS,
    )

    get_resp = await client.get(f"{BASE}/{cr_id}")
    assert get_resp.status_code == 404, get_resp.text

    patch_resp = await client.patch(
        f"{BASE}/{cr_id}", json={"status": "completed"}
    )
    assert patch_resp.status_code == 404, patch_resp.text

    del_resp = await client.delete(f"{BASE}/{cr_id}")
    assert del_resp.status_code == 404, del_resp.text


async def test_org_less_actor_rejected(client):
    p_id = await create_test_patient(client)

    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=COMM_PERMS,
    )

    resp = await client.post(BASE + "/", json=minimal_communication_request(p_id))
    assert resp.status_code == 403, resp.text

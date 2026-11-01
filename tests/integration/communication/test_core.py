"""Core Communication endpoint coverage.

Communication has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_communication,
    assert_paginated,
    assert_plain_communication,
)
from tests.integration.communication.support import (
    BASE,
    FHIR_ACCEPT,
    create_test_condition,
    create_test_encounter,
    create_test_observation,
    create_test_organization,
    create_test_patient,
    create_test_practitioner,
    full_communication,
    minimal_communication,
)

COMM_PERMS = [
    "communication:create",
    "communication:read",
    "communication:update",
    "communication:delete",
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


async def create_comm(client, patient_id: int) -> int:
    """Helper to create a minimal Communication and return public ID."""
    resp = await client.post(BASE + "/", json=minimal_communication(patient_id))
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_communication_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_communication(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_communication(data)
    assert data["subject"] == f"Patient/{p_id}"
    assert data["status"] == "completed"
    assert data["id"] >= 480000


async def test_create_communication_full(client):
    p_id = await create_test_patient(client)
    pr_id = await create_test_practitioner(client)
    org_id = await create_test_organization(client)
    enc_id = await create_test_encounter(client, p_id)
    c_id = await create_test_condition(client, p_id)

    payload = full_communication(
        p_id, pr_id, org_id, enc_id, c_id
    )
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_communication(data)
    assert data["status"] == "completed"
    assert data["priority"] == "routine"
    assert data["subject"] == f"Patient/{p_id}"
    assert data["encounter"] == f"Encounter/{enc_id}"
    assert data["sender"] == f"Practitioner/{pr_id}"
    assert data["topic_text"] == "Annual Wellness Visit Follow-up"
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
    assert data["identifier"][0]["value"] == "COMM-12345"
    assert data["instantiates_canonical"] == ["http://example.org/fhir/Questionnaire/example"]
    assert data["instantiates_uri"] == ["http://example.org/protocols/protocol1"]


async def test_create_communication_fhir(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/", json=minimal_communication(p_id), headers=FHIR_ACCEPT
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_communication(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "completed"


async def test_create_communication_invalid_subject_fails(client):
    resp = await client.post(
        BASE + "/",
        json={
            "status": "completed",
            "subject": "Patient/999999",
        },
    )
    assert resp.status_code == 422, resp.text


async def test_create_communication_missing_required(client):
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


async def test_get_communication_plain(client):
    p_id = await create_test_patient(client)
    c_id = await create_comm(client, p_id)
    resp = await client.get(f"{BASE}/{c_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_communication(data, id=c_id)
    assert data["status"] == "completed"


async def test_get_communication_fhir(client):
    p_id = await create_test_patient(client)
    c_id = await create_comm(client, p_id)
    resp = await client.get(f"{BASE}/{c_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_communication(data, id=str(c_id))
    assert data["status"] == "completed"


async def test_get_communication_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert resp.status_code == 404, resp.text


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_communication_fields(client):
    p_id = await create_test_patient(client)
    c_id = await create_comm(client, p_id)

    resp = await client.patch(
        f"{BASE}/{c_id}",
        json={
            "status": "in-progress",
            "priority": "urgent",
            "topic_text": "Updated topic",
            "status_reason_text": "Call attempted",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "in-progress"
    assert data["priority"] == "urgent"
    assert data["topic_text"] == "Updated topic"
    assert data["status_reason_text"] == "Call attempted"


async def test_patch_communication_sub_lists_replace(client):
    p_id = await create_test_patient(client)
    c_id = await create_comm(client, p_id)

    # Patch with new payload and new note
    resp = await client.patch(
        f"{BASE}/{c_id}",
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


async def test_patch_communication_not_found(client):
    resp = await client.patch(
        f"{BASE}/999999",
        json={"status": "completed"},
    )
    assert resp.status_code == 404, resp.text


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_communications_plain(client):
    p_id = await create_test_patient(client)
    await create_comm(client, p_id)

    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    assert any(c["subject"] == f"Patient/{p_id}" for c in data["data"])


async def test_list_communications_fhir(client):
    p_id = await create_test_patient(client)
    await create_comm(client, p_id)

    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)


async def test_list_communications_filter_subject(client):
    p1 = await create_test_patient(client)
    p2 = await create_test_patient(client)
    await create_comm(client, p1)
    await create_comm(client, p2)

    resp = await client.get(BASE + f"/?subject=Patient/{p1}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] == 1
    assert data["data"][0]["subject"] == f"Patient/{p1}"


async def test_list_communications_filter_status(client):
    p_id = await create_test_patient(client)
    c_id = await create_comm(client, p_id)

    await client.patch(f"{BASE}/{c_id}", json={"status": "in-progress"})

    resp = await client.get(BASE + "/?status=in-progress")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert any(c["id"] == c_id for c in data["data"])

    resp_stopped = await client.get(BASE + "/?status=stopped")
    assert resp_stopped.status_code == 200, resp_stopped.text
    data_stopped = resp_stopped.json()
    assert not any(c["id"] == c_id for c in data_stopped["data"])


async def test_list_communications_filter_priority(client):
    p_id = await create_test_patient(client)
    c_id = await create_comm(client, p_id)

    await client.patch(f"{BASE}/{c_id}", json={"priority": "urgent"})

    resp = await client.get(BASE + "/?priority=urgent")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert any(c["id"] == c_id for c in data["data"])

    resp_asap = await client.get(BASE + "/?priority=asap")
    assert resp_asap.status_code == 200, resp_asap.text
    data_asap = resp_asap.json()
    assert not any(c["id"] == c_id for c in data_asap["data"])


async def test_list_communications_pagination(client):
    p_id = await create_test_patient(client)
    await create_comm(client, p_id)
    await create_comm(client, p_id)

    resp = await client.get(BASE + f"/?subject=Patient/{p_id}&limit=1&offset=0")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["limit"] == 1
    assert len(data["data"]) == 1
    assert data["total"] >= 2


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_communication(client):
    p_id = await create_test_patient(client)
    c_id = await create_comm(client, p_id)

    resp = await client.delete(f"{BASE}/{c_id}")
    assert resp.status_code == 204, resp.text

    get_resp = await client.get(f"{BASE}/{c_id}")
    assert get_resp.status_code == 404, get_resp.text


async def test_delete_communication_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert resp.status_code == 404, resp.text


# ── Auth & Isolation ─────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    p_id = await create_test_patient(client)
    c_id = await create_comm(client, p_id)

    # Switch to different organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-other",
        permissions=COMM_PERMS,
    )

    get_resp = await client.get(f"{BASE}/{c_id}")
    assert get_resp.status_code == 404, get_resp.text

    patch_resp = await client.patch(
        f"{BASE}/{c_id}", json={"status": "in-progress"}
    )
    assert patch_resp.status_code == 404, patch_resp.text

    del_resp = await client.delete(f"{BASE}/{c_id}")
    assert del_resp.status_code == 404, del_resp.text


async def test_org_less_actor_rejected(client):
    p_id = await create_test_patient(client)

    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=COMM_PERMS,
    )

    resp = await client.post(BASE + "/", json=minimal_communication(p_id))
    assert resp.status_code == 403, resp.text

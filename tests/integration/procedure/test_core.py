"""Core procedure endpoint coverage.

Procedure has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_procedure,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_procedure,
)
from tests.integration.procedure.support import (
    BASE,
    FHIR_ACCEPT,
    create_procedure,
    create_test_condition,
    create_test_location,
    create_test_patient,
    create_test_practitioner,
    full_procedure,
    minimal_procedure,
)

PROCEDURE_PERMS = [
    "procedure:create",
    "procedure:read",
    "procedure:update",
    "procedure:delete",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "condition:create",
    "condition:read",
    "location:create",
    "location:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_procedure_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_procedure(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_procedure(data)
    assert data["subject"] == f"Patient/{p_id}"
    assert data["status"] == "completed"


async def test_create_procedure_full(client):
    p_id = await create_test_patient(client)
    pr_id = await create_test_practitioner(client)
    c_id = await create_test_condition(client, p_id)
    loc_id = await create_test_location(client)
    payload = full_procedure(p_id, pr_id, c_id, loc_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_procedure(data)
    assert data["status"] == "completed"
    assert data["category"]["text"] == "Surgical procedure"
    assert data["code"]["text"] == "Appendectomy"
    assert data["outcome"]["text"] == "Successful"
    assert len(data["reason_code"]) == 1
    assert data["reason_code"][0]["text"] == "Acute appendicitis"
    assert len(data["body_site"]) == 1
    assert data["body_site"][0]["text"] == "Appendix structure"
    assert len(data["performer"]) == 1
    assert data["performer"][0]["actor"] == f"Practitioner/{pr_id}"
    assert data["performer"][0]["actor_display"] == "Dr. Jack Surgeon"
    assert data["location"] == f"Location/{loc_id}"
    assert data["location_display"] == "Operating Room 1"
    assert len(data["reason_reference"]) == 1
    assert data["reason_reference"][0] == f"Condition/{c_id}"
    assert len(data["note"]) == 1
    assert "Procedure carried out" in data["note"][0]["text"]


async def test_create_procedure_fhir_content_negotiation(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/",
        json=minimal_procedure(p_id),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_procedure(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "completed"


async def test_create_procedure_reference_validation_nonexistent_patient(client):
    resp = await client.post(
        BASE + "/",
        json={"status": "completed", "subject": "Patient/9999999"},
    )
    assert resp.status_code == 422, resp.text


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_procedure_plain(client):
    p_id = await create_test_patient(client)
    created = await create_procedure(client, minimal_procedure(p_id))
    proc_id = created["id"]

    resp = await client.get(f"{BASE}/{proc_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_procedure(data)
    assert data["id"] == proc_id
    assert data["subject"] == f"Patient/{p_id}"


async def test_get_procedure_fhir(client):
    p_id = await create_test_patient(client)
    created = await create_procedure(client, minimal_procedure(p_id))
    proc_id = created["id"]

    resp = await client.get(f"{BASE}/{proc_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_procedure(data)
    assert data["id"] == str(proc_id)
    assert data["subject"]["reference"] == f"Patient/{p_id}"


async def test_get_procedure_not_found(client):
    resp = await client.get(f"{BASE}/9999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_procedure_scalar_and_collections(client):
    p_id = await create_test_patient(client)
    created = await create_procedure(client, minimal_procedure(p_id))
    proc_id = created["id"]

    patch_payload = {
        "status": "in-progress",
        "code": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "80146002",
                    "display": "Appendectomy",
                }
            ],
            "text": "Appendectomy",
        },
        "note": [
            {"text": "Patient prepped for surgery.", "author_string": "Nurse Kelly"}
        ],
    }

    resp = await client.patch(f"{BASE}/{proc_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_procedure(data)
    assert data["status"] == "in-progress"
    assert data["code"]["text"] == "Appendectomy"
    assert len(data["note"]) == 1
    assert data["note"][0]["text"] == "Patient prepped for surgery."

    # Replace collection
    resp2 = await client.patch(
        f"{BASE}/{proc_id}",
        json={
            "note": [
                {"text": "Surgery successfully concluded.", "author_string": "Dr. Smith"}
            ]
        },
    )
    assert resp2.status_code == 200, resp2.text
    data2 = resp2.json()
    assert len(data2["note"]) == 1
    assert data2["note"][0]["text"] == "Surgery successfully concluded."


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_procedures_plain(client):
    p_id = await create_test_patient(client)
    await create_procedure(client, minimal_procedure(p_id))

    resp = await client.get(f"{BASE}/?limit=10")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data, min_total=1)
    assert_plain_procedure(data["data"][0])


async def test_list_procedures_fhir_bundle(client):
    p_id = await create_test_patient(client)
    await create_procedure(client, minimal_procedure(p_id))

    resp = await client.get(f"{BASE}/?limit=10", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data, min_total=1)
    assert_fhir_procedure(data["entry"][0]["resource"])


async def test_list_procedures_filters(client):
    p_id = await create_test_patient(client)
    created = await create_procedure(
        client,
        {
            "status": "stopped",
            "subject": f"Patient/{p_id}",
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "TEST-CODE-123",
                        "display": "Test Procedure",
                    }
                ],
                "text": "Test Procedure",
            },
        },
    )
    proc_id = created["id"]

    # Filter by status
    resp = await client.get(f"{BASE}/?status=stopped")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert proc_id in ids

    # Filter by patient
    resp = await client.get(f"{BASE}/?patient=Patient/{p_id}")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert proc_id in ids

    # Filter by code
    resp = await client.get(f"{BASE}/?code=TEST-CODE-123")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert proc_id in ids


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_procedure(client):
    p_id = await create_test_patient(client)
    created = await create_procedure(client, minimal_procedure(p_id))
    proc_id = created["id"]

    del_resp = await client.delete(f"{BASE}/{proc_id}")
    assert del_resp.status_code == 204, del_resp.text

    get_resp = await client.get(f"{BASE}/{proc_id}")
    assert get_resp.status_code == 404


# ── Multi-Tenancy & Auth ──────────────────────────────────────────────────


async def test_procedure_cross_org_isolation(client):
    """Resource created under org-1 returns 404 (not 403) to a caller in org-2."""
    p_id = await create_test_patient(client)
    created = await create_procedure(client, minimal_procedure(p_id))
    proc_id = created["id"]

    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="different-org-id",
        permissions=PROCEDURE_PERMS,
    )
    try:
        resp = await client.get(f"{BASE}/{proc_id}")
        assert resp.status_code == 404, resp.text
        assert_operation_outcome(resp.json(), 404, resp.status_code)

        patch_resp = await client.patch(
            f"{BASE}/{proc_id}", json={"status": "in-progress"}
        )
        assert patch_resp.status_code == 404

        del_resp = await client.delete(f"{BASE}/{proc_id}")
        assert del_resp.status_code == 404
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=PROCEDURE_PERMS
        )


async def test_procedure_org_less_token_rejected(client):
    """An org-less token is rejected with 403 on create and list."""
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=PROCEDURE_PERMS,
    )
    try:
        resp = await client.post(
            BASE + "/",
            json={"status": "completed", "subject": "Patient/10001"},
        )
        assert resp.status_code == 403, resp.text

        list_resp = await client.get(BASE + "/")
        assert list_resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=PROCEDURE_PERMS
        )

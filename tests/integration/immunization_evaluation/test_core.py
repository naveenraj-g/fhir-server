"""Core ImmunizationEvaluation endpoint integration coverage.

Covers:
- create (minimal + full nested payload, FHIR format, validation, reference checks)
- read (plain + FHIR, not found)
- patch (field updates, choice type updates, not found)
- list (plain, FHIR bundle, filters, pagination)
- delete
- auth: cross-org isolation, org-less rejection, forbidden user_id
"""

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import (
    assert_fhir_bundle,
    assert_fhir_immunization_evaluation,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_immunization_evaluation,
)
from tests.integration.immunization_evaluation.support import (
    BASE,
    FHIR_ACCEPT,
    create_immunization_evaluation,
    create_test_immunization,
    create_test_organization,
    create_test_patient,
    full_immunization_evaluation,
    minimal_immunization_evaluation,
)

IMMUNIZATION_EVALUATION_PERMS = [
    "immunization_evaluation:create",
    "immunization_evaluation:read",
    "immunization_evaluation:update",
    "immunization_evaluation:delete",
    "patient:create",
    "patient:read",
    "immunization:create",
    "immunization:read",
    "organization:create",
    "organization:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_immunization_evaluation_minimal(client):
    patient_id = await create_test_patient(client)
    imm_id = await create_test_immunization(client, patient_id)

    payload = minimal_immunization_evaluation(patient_id, imm_id)
    resp = await client.post(f"{BASE}/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_immunization_evaluation(data, status="completed")
    assert data["patient"]["reference"] == f"Patient/{patient_id}"
    assert data["immunization_event"]["reference"] == f"Immunization/{imm_id}"
    assert data["target_disease"]["text"] == "Measles"
    assert data["dose_status"]["text"] == "Valid"


async def test_create_immunization_evaluation_full(client):
    patient_id = await create_test_patient(client)
    imm_id = await create_test_immunization(client, patient_id)
    org_id = await create_test_organization(client)

    payload = full_immunization_evaluation(patient_id, imm_id, org_id)
    resp = await client.post(f"{BASE}/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_immunization_evaluation(data, status="completed")
    assert data["authority"]["reference"] == f"Organization/{org_id}"
    assert data["dose_number_positive_int"] == 1
    assert data["series_doses_positive_int"] == 2
    assert data["series"] == "MMR standard series"
    assert len(data["dose_status_reason"]) == 1
    assert data["dose_status_reason"][0]["text"] == "Valid administration per guidelines"
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "EVAL-12345"


async def test_create_immunization_evaluation_fhir_accept(client):
    patient_id = await create_test_patient(client)
    imm_id = await create_test_immunization(client, patient_id)

    payload = minimal_immunization_evaluation(patient_id, imm_id)
    resp = await client.post(f"{BASE}/", json=payload, headers=FHIR_ACCEPT)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_immunization_evaluation(data, status="completed")
    assert data["resourceType"] == "ImmunizationEvaluation"
    assert data["patient"]["reference"] == f"Patient/{patient_id}"
    assert data["immunizationEvent"]["reference"] == f"Immunization/{imm_id}"


async def test_create_immunization_evaluation_invalid_reference(client):
    patient_id = await create_test_patient(client)
    # 999999 doesn't exist
    payload = minimal_immunization_evaluation(patient_id, 999999)
    resp = await client.post(f"{BASE}/", json=payload)
    assert resp.status_code in (422, 400), resp.text


async def test_create_immunization_evaluation_missing_required(client):
    # Missing required target_disease, dose_status, immunization_event
    resp = await client.post(
        f"{BASE}/",
        json={"status": "completed"},
    )
    assert resp.status_code == 422


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_immunization_evaluation_plain(client):
    patient_id = await create_test_patient(client)
    imm_id = await create_test_immunization(client, patient_id)
    eval_id = await create_immunization_evaluation(client, patient_id, imm_id)

    resp = await client.get(f"{BASE}/{eval_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_immunization_evaluation(data, id=eval_id, status="completed")


async def test_get_immunization_evaluation_fhir(client):
    patient_id = await create_test_patient(client)
    imm_id = await create_test_immunization(client, patient_id)
    eval_id = await create_immunization_evaluation(client, patient_id, imm_id)

    resp = await client.get(f"{BASE}/{eval_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_immunization_evaluation(data, id=str(eval_id), status="completed")


async def test_get_immunization_evaluation_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_immunization_evaluation_fields(client):
    patient_id = await create_test_patient(client)
    imm_id = await create_test_immunization(client, patient_id)
    eval_id = await create_immunization_evaluation(client, patient_id, imm_id)

    patch_payload = {
        "status": "entered-in-error",
        "description": "Entered in error by mistake",
    }
    resp = await client.patch(f"{BASE}/{eval_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "entered-in-error"
    assert data["description"] == "Entered in error by mistake"


async def test_patch_immunization_evaluation_choice_fields(client):
    patient_id = await create_test_patient(client)
    imm_id = await create_test_immunization(client, patient_id)
    eval_id = await create_immunization_evaluation(client, patient_id, imm_id)

    patch_payload = {
        "dose_number_string": "1 of 2",
        "series_doses_string": "2 doses",
    }
    resp = await client.patch(f"{BASE}/{eval_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["dose_number_string"] == "1 of 2"
    assert data["series_doses_string"] == "2 doses"


async def test_patch_immunization_evaluation_not_found(client):
    resp = await client.patch(
        f"{BASE}/999999",
        json={"status": "entered-in-error"},
    )
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_immunization_evaluations_plain(client):
    patient_id = await create_test_patient(client)
    imm_id = await create_test_immunization(client, patient_id)
    await create_immunization_evaluation(client, patient_id, imm_id)

    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    assert len(data["data"]) >= 1


async def test_list_immunization_evaluations_fhir_bundle(client):
    patient_id = await create_test_patient(client)
    imm_id = await create_test_immunization(client, patient_id)
    await create_immunization_evaluation(client, patient_id, imm_id)

    resp = await client.get(f"{BASE}/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    assert len(data["entry"]) >= 1
    assert data["entry"][0]["resource"]["resourceType"] == "ImmunizationEvaluation"


async def test_list_immunization_evaluations_filter_status(client):
    patient_id = await create_test_patient(client)
    imm_id = await create_test_immunization(client, patient_id)
    await create_immunization_evaluation(client, patient_id, imm_id)

    resp = await client.get(f"{BASE}/?status=completed")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    for item in data["data"]:
        assert item["status"] == "completed"

    resp = await client.get(f"{BASE}/?status=entered-in-error")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    for item in data["data"]:
        assert item["status"] == "entered-in-error"


async def test_list_immunization_evaluations_filter_patient(client):
    patient_id = await create_test_patient(client)
    imm_id = await create_test_immunization(client, patient_id)
    eval_id = await create_immunization_evaluation(client, patient_id, imm_id)

    resp = await client.get(f"{BASE}/?patient=Patient/{patient_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert any(item["id"] == eval_id for item in data["data"])


async def test_list_immunization_evaluations_pagination(client):
    patient_id = await create_test_patient(client)
    imm_id = await create_test_immunization(client, patient_id)
    await create_immunization_evaluation(client, patient_id, imm_id)

    resp = await client.get(f"{BASE}/?limit=1&offset=0")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["limit"] == 1
    assert len(data["data"]) <= 1


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_immunization_evaluation(client):
    patient_id = await create_test_patient(client)
    imm_id = await create_test_immunization(client, patient_id)
    eval_id = await create_immunization_evaluation(client, patient_id, imm_id)

    resp = await client.delete(f"{BASE}/{eval_id}")
    assert resp.status_code == 204

    # Verification: should be gone (404)
    resp = await client.get(f"{BASE}/{eval_id}")
    assert resp.status_code == 404


async def test_delete_immunization_evaluation_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Multi-Tenancy & RBAC ─────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    # Create in org-primary (default)
    patient_id = await create_test_patient(client)
    imm_id = await create_test_immunization(client, patient_id)
    eval_id = await create_immunization_evaluation(client, patient_id, imm_id)

    # Switch to different organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="other-org",
        permissions=IMMUNIZATION_EVALUATION_PERMS,
    )
    try:
        # Cross-org GET must return 404 (never 403)
        resp = await client.get(f"{BASE}/{eval_id}")
        assert resp.status_code == 404
        assert_operation_outcome(resp.json(), 404, resp.status_code)

        # Cross-org PATCH must return 404
        resp = await client.patch(
            f"{BASE}/{eval_id}",
            json={"status": "entered-in-error"},
        )
        assert resp.status_code == 404

        # Cross-org DELETE must return 404
        resp = await client.delete(f"{BASE}/{eval_id}")
        assert resp.status_code == 404

        # Cross-org list should not contain this record
        resp = await client.get(f"{BASE}/")
        assert resp.status_code == 200
        assert not any(item["id"] == eval_id for item in resp.json()["data"])
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=IMMUNIZATION_EVALUATION_PERMS
        )


async def test_org_less_actor_rejected(client):
    # Org-less user (no activeOrganizationId claim)
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=IMMUNIZATION_EVALUATION_PERMS,
    )
    try:
        resp = await client.post(
            f"{BASE}/",
            json={
                "status": "completed",
                "patient": {"reference": "Patient/10001"},
                "target_disease": {"text": "Measles"},
                "immunization_event": {"reference": "Immunization/330001"},
                "dose_status": {"text": "Valid"},
            },
        )
        assert resp.status_code == 403

        resp = await client.get(f"{BASE}/")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=IMMUNIZATION_EVALUATION_PERMS
        )


async def test_user_id_forbidden_in_payload(client):
    patient_id = await create_test_patient(client)
    imm_id = await create_test_immunization(client, patient_id)

    payload = minimal_immunization_evaluation(patient_id, imm_id)
    # Extra forbidden field: user_id
    payload["user_id"] = "user-123"

    resp = await client.post(f"{BASE}/", json=payload)
    # Extra field forbidden -> 422
    assert resp.status_code == 422

"""Core RiskAssessment endpoint coverage.

RiskAssessment has 5 endpoints (create/get/patch/list/delete),
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
    assert_fhir_risk_assessment,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_risk_assessment,
)
from tests.integration.risk_assessment.support import (
    BASE,
    FHIR_ACCEPT,
    create_risk_assessment,
    create_test_condition,
    create_test_encounter,
    create_test_patient,
    create_test_practitioner,
    full_risk_assessment,
    minimal_risk_assessment,
)

RISK_ASSESSMENT_PERMS = [
    "risk_assessment:create",
    "risk_assessment:read",
    "risk_assessment:update",
    "risk_assessment:delete",
    "patient:create",
    "patient:read",
    "condition:create",
    "condition:read",
    "practitioner:create",
    "practitioner:read",
    "encounter:create",
    "encounter:read",
    "organization:create",
    "organization:read",
    "observation:create",
    "observation:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_risk_assessment_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_risk_assessment(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_risk_assessment(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["id"] >= 520000
    assert data["status"] == "final"


async def test_create_risk_assessment_full(client):
    p_id = await create_test_patient(client)
    cond_id = await create_test_condition(client, p_id)
    pract_id = await create_test_practitioner(client)
    enc_id = await create_test_encounter(client, p_id)

    payload = full_risk_assessment(
        p_id,
        condition_id=cond_id,
        practitioner_id=pract_id,
        encounter_id=enc_id,
    )
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_risk_assessment(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["condition"]["reference"] == f"Condition/{cond_id}"
    assert data["performer"]["reference"] == f"Practitioner/{pract_id}"
    assert data["encounter"]["reference"] == f"Encounter/{enc_id}"
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "RA-2026-001"
    assert data["method"]["text"] == "Framingham 10-year risk assessment"
    assert data["code"]["text"] == "Cardiovascular disease 10Y risk"
    assert len(data["prediction"]) == 1

    pred = data["prediction"][0]
    assert pred["outcome"]["text"] == "Atrial fibrillation"
    assert pred["probability_decimal"] == 0.12
    assert pred["qualitative_risk"]["text"] == "Moderate risk"
    assert pred["relative_risk"] == 1.5
    assert pred["rationale"] == "Elevated systolic BP and family history."
    assert data["mitigation"] == "Lifestyle modifications and low-dose antihypertensive therapy."
    assert len(data["note"]) == 1
    assert data["note"][0]["text"] == "Re-evaluate in 12 months."


async def test_create_risk_assessment_fhir(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/",
        json=minimal_risk_assessment(p_id),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_risk_assessment(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "final"


async def test_create_risk_assessment_invalid_subject_422(client):
    resp = await client.post(
        BASE + "/",
        json=minimal_risk_assessment(99999999),
    )
    assert resp.status_code == 422, resp.text
    assert "subject" in resp.text.lower()


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_risk_assessment_plain(client):
    p_id = await create_test_patient(client)
    ra_id = await create_risk_assessment(client, p_id)

    resp = await client.get(f"{BASE}/{ra_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_risk_assessment(data, id=ra_id)
    assert data["subject"]["reference"] == f"Patient/{p_id}"


async def test_get_risk_assessment_fhir(client):
    p_id = await create_test_patient(client)
    ra_id = await create_risk_assessment(client, p_id)

    resp = await client.get(f"{BASE}/{ra_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_risk_assessment(data, id=str(ra_id))
    assert data["subject"]["reference"] == f"Patient/{p_id}"


async def test_get_risk_assessment_not_found(client):
    resp = await client.get(f"{BASE}/99999999")
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_risk_assessment_fields(client):
    p_id = await create_test_patient(client)
    ra_id = await create_risk_assessment(client, p_id)

    patch_payload = {
        "status": "amended",
        "mitigation": "Annual cardiac checkup.",
    }
    resp = await client.patch(f"{BASE}/{ra_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_risk_assessment(data, id=ra_id)
    assert data["status"] == "amended"
    assert data["mitigation"] == "Annual cardiac checkup."


async def test_patch_risk_assessment_replace_predictions(client):
    p_id = await create_test_patient(client)
    ra_id = await create_risk_assessment(client, p_id)

    new_pred = [
        {
            "outcome": {
                "text": "Heart failure",
            },
            "probability_decimal": 0.05,
            "rationale": "Low risk based on recent labs.",
        }
    ]
    resp = await client.patch(f"{BASE}/{ra_id}", json={"prediction": new_pred})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_risk_assessment(data, id=ra_id)
    assert len(data["prediction"]) == 1
    assert data["prediction"][0]["outcome"]["text"] == "Heart failure"
    assert data["prediction"][0]["probability_decimal"] == 0.05
    assert data["prediction"][0]["rationale"] == "Low risk based on recent labs."


async def test_patch_risk_assessment_not_found(client):
    resp = await client.patch(
        f"{BASE}/99999999",
        json={"status": "amended"},
    )
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_risk_assessments_plain(client):
    p_id = await create_test_patient(client)
    ra_id = await create_risk_assessment(client, p_id)

    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    ids = [item["id"] for item in data["data"]]
    assert ra_id in ids


async def test_list_risk_assessments_fhir_bundle(client):
    p_id = await create_test_patient(client)
    ra_id = await create_risk_assessment(client, p_id)

    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    resource_ids = [entry["resource"]["id"] for entry in data.get("entry", [])]
    assert str(ra_id) in resource_ids


async def test_list_risk_assessments_filter_subject(client):
    p1 = await create_test_patient(client)
    p2 = await create_test_patient(client)
    r1 = await create_risk_assessment(client, p1)
    r2 = await create_risk_assessment(client, p2)

    resp = await client.get(f"{BASE}/?subject=Patient/{p1}")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert r1 in ids
    assert r2 not in ids


async def test_list_risk_assessments_filter_status(client):
    p_id = await create_test_patient(client)
    ra_id = await create_risk_assessment(client, p_id)

    resp = await client.get(f"{BASE}/?status=final")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert ra_id in ids

    resp2 = await client.get(f"{BASE}/?status=preliminary")
    assert resp2.status_code == 200, resp2.text
    ids2 = [item["id"] for item in resp2.json()["data"]]
    assert ra_id not in ids2


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_risk_assessment(client):
    p_id = await create_test_patient(client)
    ra_id = await create_risk_assessment(client, p_id)

    resp = await client.delete(f"{BASE}/{ra_id}")
    assert resp.status_code == 204

    resp = await client.get(f"{BASE}/{ra_id}")
    assert resp.status_code == 404


async def test_delete_risk_assessment_not_found(client):
    resp = await client.delete(f"{BASE}/99999999")
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Auth & Isolation ─────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    p_id = await create_test_patient(client)
    ra_id = await create_risk_assessment(client, p_id)

    # Switch token to another organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="other-org",
        permissions=RISK_ASSESSMENT_PERMS,
    )

    # GET must 404 (never leak cross-tenant existence)
    resp = await client.get(f"{BASE}/{ra_id}")
    assert resp.status_code == 404

    # PATCH must 404
    resp = await client.patch(f"{BASE}/{ra_id}", json={"mitigation": "Different org patch"})
    assert resp.status_code == 404

    # DELETE must 404
    resp = await client.delete(f"{BASE}/{ra_id}")
    assert resp.status_code == 404

    # LIST must not contain this resource
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert ra_id not in ids


async def test_org_less_token_rejected_403(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=RISK_ASSESSMENT_PERMS,
    )

    resp = await client.post(
        BASE + "/",
        json=minimal_risk_assessment(10001),
    )
    assert resp.status_code == 403
    assert_operation_outcome(resp.json(), 403, resp.status_code)

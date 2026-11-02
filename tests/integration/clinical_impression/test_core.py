"""Core ClinicalImpression endpoint coverage.

ClinicalImpression has 5 endpoints (create/get/patch/list/delete),
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
    assert_fhir_clinical_impression,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_clinical_impression,
)
from tests.integration.clinical_impression.support import (
    BASE,
    FHIR_ACCEPT,
    create_clinical_impression,
    create_test_condition,
    create_test_encounter,
    create_test_observation,
    create_test_patient,
    create_test_practitioner,
    create_test_risk_assessment,
    full_clinical_impression,
    minimal_clinical_impression,
)

CLINICAL_IMPRESSION_PERMS = [
    "clinical_impression:create",
    "clinical_impression:read",
    "clinical_impression:update",
    "clinical_impression:delete",
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
    "risk_assessment:create",
    "risk_assessment:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_clinical_impression_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_clinical_impression(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_clinical_impression(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["id"] >= 530000
    assert data["status"] == "completed"


async def test_create_clinical_impression_full(client):
    p_id = await create_test_patient(client)
    cond_id = await create_test_condition(client, p_id)
    pract_id = await create_test_practitioner(client)
    enc_id = await create_test_encounter(client, p_id)
    obs_id = await create_test_observation(client, p_id)
    ra_id = await create_test_risk_assessment(client, p_id)

    payload = full_clinical_impression(
        p_id,
        encounter_id=enc_id,
        practitioner_id=pract_id,
        condition_id=cond_id,
        observation_id=obs_id,
        risk_assessment_id=ra_id,
    )
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_clinical_impression(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["encounter"]["reference"] == f"Encounter/{enc_id}"
    assert data["assessor"]["reference"] == f"Practitioner/{pract_id}"
    assert len(data["problem"]) == 1
    assert data["problem"][0]["reference"] == f"Condition/{cond_id}"
    assert len(data["prognosis_reference"]) == 1
    assert data["prognosis_reference"][0]["reference"] == f"RiskAssessment/{ra_id}"
    assert len(data["supporting_info"]) == 1
    assert data["supporting_info"][0]["reference"] == f"Observation/{obs_id}"
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "CI-2026-001"
    assert data["description"] == "Initial clinical evaluation for chest pain."
    assert data["summary"] == "Non-cardiac chest pain; musculoskeletal in origin."
    assert data["status_reason"]["text"] == "Evaluation finished and treatment plan established"
    assert data["code"]["text"] == "Initial acute assessment"
    assert data["protocol"] == ["http://example.org/protocols/chest-pain-eval"]
    assert len(data["investigation"]) == 1
    assert data["investigation"][0]["code"]["text"] == "Initial physical exam"
    assert len(data["investigation"][0]["item"]) == 1
    assert data["investigation"][0]["item"][0]["reference"] == f"Observation/{obs_id}"
    assert len(data["finding"]) == 1
    assert data["finding"][0]["item_codeable_concept"]["text"] == "Musculoskeletal chest wall tenderness"
    assert data["finding"][0]["item_reference"]["reference"] == f"Condition/{cond_id}"
    assert data["finding"][0]["basis"] == "Point tenderness on palpation; normal ECG"
    assert len(data["prognosis_codeable_concept"]) == 1
    assert data["prognosis_codeable_concept"][0]["text"] == "Full recovery expected within 1-2 weeks"
    assert len(data["note"]) == 1
    assert data["note"][0]["text"] == "Advised gentle stretching and NSAIDs as needed."


async def test_create_clinical_impression_fhir(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/",
        json=minimal_clinical_impression(p_id),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_clinical_impression(data)
    assert data["subject"]["reference"] == f"Patient/{p_id}"
    assert data["status"] == "completed"


async def test_create_clinical_impression_invalid_subject_422(client):
    resp = await client.post(
        BASE + "/",
        json=minimal_clinical_impression(99999999),
    )
    assert resp.status_code == 422, resp.text
    assert "subject" in resp.text.lower()


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_clinical_impression_plain(client):
    p_id = await create_test_patient(client)
    ci_id = await create_clinical_impression(client, p_id)

    resp = await client.get(f"{BASE}/{ci_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_clinical_impression(data, id=ci_id)
    assert data["subject"]["reference"] == f"Patient/{p_id}"


async def test_get_clinical_impression_fhir(client):
    p_id = await create_test_patient(client)
    ci_id = await create_clinical_impression(client, p_id)

    resp = await client.get(f"{BASE}/{ci_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_clinical_impression(data, id=str(ci_id))
    assert data["subject"]["reference"] == f"Patient/{p_id}"


async def test_get_clinical_impression_not_found(client):
    resp = await client.get(f"{BASE}/99999999")
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_clinical_impression_fields(client):
    p_id = await create_test_patient(client)
    ci_id = await create_clinical_impression(client, p_id)

    patch_payload = {
        "status": "in-progress",
        "description": "Updated evaluation progress.",
        "summary": "Pending further lab results.",
    }
    resp = await client.patch(f"{BASE}/{ci_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_clinical_impression(data, id=ci_id)
    assert data["status"] == "in-progress"
    assert data["description"] == "Updated evaluation progress."
    assert data["summary"] == "Pending further lab results."


async def test_patch_clinical_impression_replace_investigations(client):
    p_id = await create_test_patient(client)
    ci_id = await create_clinical_impression(client, p_id)

    new_investigations = [
        {
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "160244002",
                        "display": "No history of chest pain",
                    }
                ],
                "text": "Secondary examination",
            },
        }
    ]
    resp = await client.patch(f"{BASE}/{ci_id}", json={"investigation": new_investigations})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_clinical_impression(data, id=ci_id)
    assert len(data["investigation"]) == 1
    assert data["investigation"][0]["code"]["text"] == "Secondary examination"


async def test_patch_clinical_impression_replace_findings(client):
    p_id = await create_test_patient(client)
    ci_id = await create_clinical_impression(client, p_id)

    new_findings = [
        {
            "item_codeable_concept": {
                "text": "Normal vital signs",
            },
            "basis": "BP 120/80, HR 72",
        }
    ]
    resp = await client.patch(f"{BASE}/{ci_id}", json={"finding": new_findings})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_clinical_impression(data, id=ci_id)
    assert len(data["finding"]) == 1
    assert data["finding"][0]["item_codeable_concept"]["text"] == "Normal vital signs"
    assert data["finding"][0]["basis"] == "BP 120/80, HR 72"


async def test_patch_clinical_impression_not_found(client):
    resp = await client.patch(
        f"{BASE}/99999999",
        json={"status": "in-progress"},
    )
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_clinical_impressions_plain(client):
    p_id = await create_test_patient(client)
    ci_id = await create_clinical_impression(client, p_id)

    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    ids = [item["id"] for item in data["data"]]
    assert ci_id in ids


async def test_list_clinical_impressions_fhir_bundle(client):
    p_id = await create_test_patient(client)
    ci_id = await create_clinical_impression(client, p_id)

    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    resource_ids = [entry["resource"]["id"] for entry in data.get("entry", [])]
    assert str(ci_id) in resource_ids


async def test_list_clinical_impressions_filter_subject(client):
    p1 = await create_test_patient(client)
    p2 = await create_test_patient(client)
    c1 = await create_clinical_impression(client, p1)
    c2 = await create_clinical_impression(client, p2)

    resp = await client.get(f"{BASE}/?subject=Patient/{p1}")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert c1 in ids
    assert c2 not in ids


async def test_list_clinical_impressions_filter_status(client):
    p_id = await create_test_patient(client)
    ci_id = await create_clinical_impression(client, p_id)

    resp = await client.get(f"{BASE}/?status=completed")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert ci_id in ids

    resp2 = await client.get(f"{BASE}/?status=in-progress")
    assert resp2.status_code == 200, resp2.text
    ids2 = [item["id"] for item in resp2.json()["data"]]
    assert ci_id not in ids2


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_clinical_impression(client):
    p_id = await create_test_patient(client)
    ci_id = await create_clinical_impression(client, p_id)

    resp = await client.delete(f"{BASE}/{ci_id}")
    assert resp.status_code == 204

    resp = await client.get(f"{BASE}/{ci_id}")
    assert resp.status_code == 404


async def test_delete_clinical_impression_not_found(client):
    resp = await client.delete(f"{BASE}/99999999")
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Auth & Isolation ─────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    p_id = await create_test_patient(client)
    ci_id = await create_clinical_impression(client, p_id)

    # Switch token to another organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="other-org",
        permissions=CLINICAL_IMPRESSION_PERMS,
    )

    # GET must 404 (never leak cross-tenant existence)
    resp = await client.get(f"{BASE}/{ci_id}")
    assert resp.status_code == 404

    # PATCH must 404
    resp = await client.patch(f"{BASE}/{ci_id}", json={"description": "Different org patch"})
    assert resp.status_code == 404

    # DELETE must 404
    resp = await client.delete(f"{BASE}/{ci_id}")
    assert resp.status_code == 404

    # LIST must not contain this resource
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert ci_id not in ids


async def test_org_less_token_rejected_403(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=CLINICAL_IMPRESSION_PERMS,
    )

    resp = await client.post(
        BASE + "/",
        json=minimal_clinical_impression(10001),
    )
    assert resp.status_code == 403
    assert_operation_outcome(resp.json(), 403, resp.status_code)

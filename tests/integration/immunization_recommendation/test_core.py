"""Core ImmunizationRecommendation endpoint coverage.

ImmunizationRecommendation has 5 endpoints (create/get/patch/list/delete),
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
    assert_fhir_immunization_recommendation,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_immunization_recommendation,
)
from tests.integration.immunization_recommendation.support import (
    BASE,
    FHIR_ACCEPT,
    create_immunization_recommendation,
    create_test_condition,
    create_test_immunization,
    create_test_organization,
    create_test_patient,
    full_immunization_recommendation,
    minimal_immunization_recommendation,
)

IMM_REC_PERMS = [
    "immunization_recommendation:create",
    "immunization_recommendation:read",
    "immunization_recommendation:update",
    "immunization_recommendation:delete",
    "patient:create",
    "patient:read",
    "organization:create",
    "organization:read",
    "immunization:create",
    "immunization:read",
    "condition:create",
    "condition:read",
    "observation:create",
    "observation:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_immunization_recommendation_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_immunization_recommendation(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_immunization_recommendation(data)
    assert data["patient"]["reference"] == f"Patient/{p_id}"
    assert data["id"] >= 510000
    assert len(data["recommendation"]) == 1
    assert data["recommendation"][0]["forecast_status"]["text"] == "Due"


async def test_create_immunization_recommendation_full(client):
    p_id = await create_test_patient(client)
    org_id = await create_test_organization(client)
    imm_id = await create_test_immunization(client, p_id)
    cond_id = await create_test_condition(client, p_id)

    payload = full_immunization_recommendation(
        p_id,
        org_id=org_id,
        immunization_id=imm_id,
        condition_id=cond_id,
    )
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_immunization_recommendation(data)
    assert data["patient"]["reference"] == f"Patient/{p_id}"
    assert data["authority"]["reference"] == f"Organization/{org_id}"
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "REC-998877"

    rec = data["recommendation"][0]
    assert rec["target_disease"]["text"] == "Influenza"
    assert rec["vaccine_code"][0]["text"] == "Fluzone High-Dose Quadrivalent"
    assert rec["contraindicated_vaccine_code"][0]["text"] == "Live Attenuated Influenza"
    assert rec["forecast_status"]["text"] == "Due"
    assert rec["forecast_reason"][0]["text"] == "Age 65+"
    assert rec["date_criterion"][0]["code"]["text"] == "Date vaccine due"
    assert rec["description"] == "Annual influenza vaccination recommended for older adults"
    assert rec["series"] == "Annual"
    assert rec["dose_number_positive_int"] == 1
    assert rec["series_doses_positive_int"] == 1
    assert rec["supporting_immunization"][0]["reference"] == f"Immunization/{imm_id}"
    assert rec["supporting_patient_information"][0]["reference"] == f"Condition/{cond_id}"


async def test_create_immunization_recommendation_fhir(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/",
        json=minimal_immunization_recommendation(p_id),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_immunization_recommendation(data)
    assert data["patient"]["reference"] == f"Patient/{p_id}"
    assert len(data["recommendation"]) == 1
    assert data["recommendation"][0]["forecastStatus"]["text"] == "Due"


async def test_create_immunization_recommendation_invalid_patient_422(client):
    resp = await client.post(
        BASE + "/",
        json=minimal_immunization_recommendation(99999999),
    )
    assert resp.status_code == 422, resp.text
    assert "patient" in resp.text.lower()


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_immunization_recommendation_plain(client):
    p_id = await create_test_patient(client)
    rec_id = await create_immunization_recommendation(client, p_id)

    resp = await client.get(f"{BASE}/{rec_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_immunization_recommendation(data, id=rec_id)
    assert data["patient"]["reference"] == f"Patient/{p_id}"


async def test_get_immunization_recommendation_fhir(client):
    p_id = await create_test_patient(client)
    rec_id = await create_immunization_recommendation(client, p_id)

    resp = await client.get(f"{BASE}/{rec_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_immunization_recommendation(data, id=str(rec_id))
    assert data["patient"]["reference"] == f"Patient/{p_id}"


async def test_get_immunization_recommendation_not_found(client):
    resp = await client.get(f"{BASE}/99999999")
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_immunization_recommendation_fields(client):
    p_id = await create_test_patient(client)
    rec_id = await create_immunization_recommendation(client, p_id)

    patch_payload = {
        "date": "2026-03-01T12:00:00Z",
    }
    resp = await client.patch(f"{BASE}/{rec_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_immunization_recommendation(data, id=rec_id)
    assert "2026-03-01" in data["date"]


async def test_patch_immunization_recommendation_replace_recommendations(client):
    p_id = await create_test_patient(client)
    rec_id = await create_immunization_recommendation(client, p_id)

    new_recommendation = [
        {
            "forecast_status": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/immunization-recommendation-status",
                        "code": "overdue",
                        "display": "Overdue",
                    }
                ],
                "text": "Overdue",
            },
            "description": "Updated recommendation to overdue",
        }
    ]
    resp = await client.patch(f"{BASE}/{rec_id}", json={"recommendation": new_recommendation})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_immunization_recommendation(data, id=rec_id)
    assert len(data["recommendation"]) == 1
    assert data["recommendation"][0]["forecast_status"]["text"] == "Overdue"
    assert data["recommendation"][0]["description"] == "Updated recommendation to overdue"


async def test_patch_immunization_recommendation_not_found(client):
    resp = await client.patch(
        f"{BASE}/99999999",
        json={"date": "2026-03-01T12:00:00Z"},
    )
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_immunization_recommendations_plain(client):
    p_id = await create_test_patient(client)
    rec_id = await create_immunization_recommendation(client, p_id)

    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    ids = [item["id"] for item in data["data"]]
    assert rec_id in ids


async def test_list_immunization_recommendations_fhir_bundle(client):
    p_id = await create_test_patient(client)
    rec_id = await create_immunization_recommendation(client, p_id)

    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    resource_ids = [entry["resource"]["id"] for entry in data.get("entry", [])]
    assert str(rec_id) in resource_ids


async def test_list_immunization_recommendations_filter_patient(client):
    p1 = await create_test_patient(client)
    p2 = await create_test_patient(client)
    r1 = await create_immunization_recommendation(client, p1)
    r2 = await create_immunization_recommendation(client, p2)

    resp = await client.get(f"{BASE}/?patient={p1}")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert r1 in ids
    assert r2 not in ids


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_immunization_recommendation(client):
    p_id = await create_test_patient(client)
    rec_id = await create_immunization_recommendation(client, p_id)

    resp = await client.delete(f"{BASE}/{rec_id}")
    assert resp.status_code == 204

    resp = await client.get(f"{BASE}/{rec_id}")
    assert resp.status_code == 404


async def test_delete_immunization_recommendation_not_found(client):
    resp = await client.delete(f"{BASE}/99999999")
    assert resp.status_code == 404
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Auth & Isolation ─────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    p_id = await create_test_patient(client)
    rec_id = await create_immunization_recommendation(client, p_id)

    # Switch token to another organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="other-org",
        permissions=IMM_REC_PERMS,
    )

    # GET must 404 (never leak cross-tenant existence)
    resp = await client.get(f"{BASE}/{rec_id}")
    assert resp.status_code == 404

    # PATCH must 404
    resp = await client.patch(f"{BASE}/{rec_id}", json={"date": "2026-03-01T12:00:00Z"})
    assert resp.status_code == 404

    # DELETE must 404
    resp = await client.delete(f"{BASE}/{rec_id}")
    assert resp.status_code == 404

    # LIST must not contain this resource
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200
    ids = [item["id"] for item in resp.json()["data"]]
    assert rec_id not in ids


async def test_org_less_token_rejected_403(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=IMM_REC_PERMS,
    )

    resp = await client.post(
        BASE + "/",
        json=minimal_immunization_recommendation(10001),
    )
    assert resp.status_code == 403
    assert_operation_outcome(resp.json(), 403, resp.status_code)

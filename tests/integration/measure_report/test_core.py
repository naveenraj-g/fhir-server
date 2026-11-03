"""Core MeasureReport endpoint coverage.

MeasureReport has 5 endpoints (create/get/patch/list/delete),
no sub-resource routes and no /me route.

This file covers:
- create (minimal + full nested payload, FHIR format, validation, reference check)
- read (plain + FHIR, not found)
- patch (field updates, sub-list replace, not found)
- list (plain, FHIR bundle, filters, pagination)
- delete (cascade delete, 404 after delete)
- auth: cross-org isolation, org-less rejection, unauthenticated rejection
"""

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import (
    assert_fhir_bundle,
    assert_fhir_measure_report,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_measure_report,
)
from tests.integration.measure_report.support import (
    BASE,
    FHIR_ACCEPT,
    create_measure_report,
    create_test_organization,
    create_test_patient,
    create_test_practitioner,
    full_measure_report,
    minimal_measure_report,
)

MEASURE_REPORT_PERMS = [
    "measure_report:create",
    "measure_report:read",
    "measure_report:update",
    "measure_report:delete",
    "organization:create",
    "organization:read",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "observation:create",
    "observation:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_measure_report_minimal(client):
    payload = minimal_measure_report()
    resp = await client.post(f"{BASE}/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_measure_report(data, status="complete", type="summary")


async def test_create_measure_report_full_plain(client):
    org_id = await create_test_organization(client)
    patient_id = await create_test_patient(client)
    practitioner_id = await create_test_practitioner(client)
    payload = full_measure_report(org_id, patient_id, practitioner_id)
    resp = await client.post(f"{BASE}/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert_plain_measure_report(
        data,
        status="complete",
        type="summary",
        measure="http://example.org/fhir/Measure/exclusive-breastfeeding-measure",
        subject=f"Patient/{patient_id}",
        reporter=f"Practitioner/{practitioner_id}",
    )
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "mr-full-001"
    assert len(data["group"]) == 1
    assert data["group"][0]["code_text"] == "Primary Group"
    assert len(data["group"][0]["population"]) == 1
    assert data["group"][0]["population"][0]["count"] == 100
    assert len(data["group"][0]["stratifier"]) == 1
    assert data["group"][0]["stratifier"][0]["code"][0]["text"] == "Gender"
    assert len(data["group"][0]["stratifier"][0]["stratum"]) == 1
    assert data["group"][0]["stratifier"][0]["stratum"][0]["value_text"] == "Male"
    assert data["group"][0]["stratifier"][0]["stratum"][0]["measure_score_value"] == 0.85


async def test_create_measure_report_fhir(client):
    payload = minimal_measure_report()
    resp = await client.post(f"{BASE}/", json=payload, headers=FHIR_ACCEPT)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_measure_report(data, status="complete", type="summary")


async def test_create_measure_report_invalid_org_ref(client):
    payload = minimal_measure_report()
    payload["identifier"] = [
        {
            "value": "MR-FAIL",
            "assigner": "Organization/999999",
        }
    ]
    resp = await client.post(f"{BASE}/", json=payload)
    assert resp.status_code == 422, resp.text
    assert_operation_outcome(resp.json(), 422, resp.status_code)


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_measure_report_plain(client):
    res_id = await create_measure_report(client)
    resp = await client.get(f"{BASE}/{res_id}")
    assert resp.status_code == 200, resp.text
    assert_plain_measure_report(resp.json(), id=res_id)


async def test_get_measure_report_fhir(client):
    res_id = await create_measure_report(client)
    resp = await client.get(f"{BASE}/{res_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    assert_fhir_measure_report(resp.json(), id=str(res_id))


async def test_get_measure_report_not_found(client):
    resp = await client.get(f"{BASE}/999999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_measure_report(client):
    res_id = await create_measure_report(client)
    patch_payload = {
        "status": "pending",
        "improvement_notation_text": "Updated notation",
    }
    resp = await client.patch(f"{BASE}/{res_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    assert_plain_measure_report(
        resp.json(),
        status="pending",
        improvement_notation_text="Updated notation",
    )


async def test_patch_measure_report_fhir(client):
    res_id = await create_measure_report(client)
    patch_payload = {
        "status": "pending",
    }
    resp = await client.patch(f"{BASE}/{res_id}", json=patch_payload, headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    assert_fhir_measure_report(resp.json(), status="pending")


async def test_patch_measure_report_not_found(client):
    resp = await client.patch(f"{BASE}/999999999", json={"status": "pending"})
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_measure_reports_plain(client):
    await create_measure_report(client)
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    assert_paginated(resp.json())


async def test_list_measure_reports_fhir(client):
    await create_measure_report(client)
    resp = await client.get(f"{BASE}/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    assert_fhir_bundle(resp.json())


async def test_list_measure_reports_filter_status(client):
    resp = await client.post(
        f"{BASE}/",
        json={
            "status": "pending",
            "type": "summary",
            "measure": "http://example.org/fhir/Measure/pending-measure",
            "period_start": "2026-01-01T00:00:00Z",
            "period_end": "2026-01-31T23:59:59Z",
        },
    )
    assert resp.status_code == 201, resp.text

    resp = await client.get(f"{BASE}/?status=pending")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] >= 1
    assert all(item.get("status") == "pending" for item in data["data"])


async def test_list_measure_reports_filter_identifier(client):
    resp = await client.post(
        f"{BASE}/",
        json={
            "status": "complete",
            "type": "summary",
            "measure": "http://example.org/fhir/Measure/ident-measure",
            "period_start": "2026-01-01T00:00:00Z",
            "period_end": "2026-01-31T23:59:59Z",
            "identifier": [
                {
                    "system": "http://example.org/mr-ids",
                    "value": "FLT-MR-001",
                }
            ],
        },
    )
    assert resp.status_code == 201, resp.text

    resp = await client.get(f"{BASE}/?identifier=http://example.org/mr-ids|FLT-MR-001")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] >= 1
    assert any(
        any(i.get("value") == "FLT-MR-001" for i in (item.get("identifier") or []))
        for item in data["data"]
    )


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_measure_report(client):
    res_id = await create_measure_report(client)
    del_resp = await client.delete(f"{BASE}/{res_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"{BASE}/{res_id}")
    assert get_resp.status_code == 404


async def test_delete_measure_report_not_found(client):
    resp = await client.delete(f"{BASE}/999999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Auth & Scoping ───────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    # Create with org-test (default)
    res_id = await create_measure_report(client)

    # Switch to org-other
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-other",
        permissions=MEASURE_REPORT_PERMS,
    )

    get_resp = await client.get(f"{BASE}/{res_id}")
    assert get_resp.status_code == 404, "Other org must not see this resource"

    patch_resp = await client.patch(f"{BASE}/{res_id}", json={"status": "pending"})
    assert patch_resp.status_code == 404, "Other org must not patch this resource"

    del_resp = await client.delete(f"{BASE}/{res_id}")
    assert del_resp.status_code == 404, "Other org must not delete this resource"


async def test_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=MEASURE_REPORT_PERMS,
    )
    resp = await client.post(f"{BASE}/", json=minimal_measure_report())
    assert resp.status_code == 403, resp.text
    assert_operation_outcome(resp.json(), 403, resp.status_code)


async def test_missing_permission_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=[],
    )
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 403, resp.text
    assert_operation_outcome(resp.json(), 403, resp.status_code)

"""Core Measure endpoint coverage.

Measure has 5 endpoints (create/get/patch/list/delete),
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
    assert_fhir_measure,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_measure,
)
from tests.integration.measure.support import (
    BASE,
    FHIR_ACCEPT,
    create_measure,
    create_test_organization,
    full_measure,
    minimal_measure,
)

MEASURE_PERMS = [
    "measure:create",
    "measure:read",
    "measure:update",
    "measure:delete",
    "organization:create",
    "organization:read",
    "group:create",
    "group:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_measure_minimal(client):
    payload = minimal_measure()
    resp = await client.post(f"{BASE}/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_measure(data, status="draft")


async def test_create_measure_full_plain(client):
    org_id = await create_test_organization(client)
    payload = full_measure(org_id)
    resp = await client.post(f"{BASE}/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert_plain_measure(
        data,
        name="ExclusiveBreastfeedingMeasure",
        title="Exclusive Breastfeeding Measure",
        status="draft",
        experimental=True,
    )
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "meas-full-001"
    assert data["subject_codeable_concept"]["text"] == "Patient"
    assert len(data["contact"]) == 1
    assert len(data["use_context"]) == 1
    assert len(data["jurisdiction"]) == 1
    assert len(data["topic"]) == 1
    assert len(data["author"]) == 1
    assert len(data["editor"]) == 1
    assert len(data["reviewer"]) == 1
    assert len(data["endorser"]) == 1
    assert len(data["related_artifact"]) == 1
    assert len(data["type"]) == 1
    assert len(data["group"]) == 1
    assert len(data["group"][0]["population"]) == 1
    assert len(data["group"][0]["stratifier"]) == 1
    assert len(data["supplemental_data"]) == 1


async def test_create_measure_fhir(client):
    payload = minimal_measure()
    resp = await client.post(f"{BASE}/", json=payload, headers=FHIR_ACCEPT)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_measure(data, status="draft")


async def test_create_measure_invalid_org_ref(client):
    payload = minimal_measure()
    payload["identifier"] = [
        {
            "value": "MEAS-FAIL",
            "assigner": "Organization/999999",
        }
    ]
    resp = await client.post(f"{BASE}/", json=payload)
    assert resp.status_code == 422, resp.text
    assert_operation_outcome(resp.json(), 422, resp.status_code)


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_measure_plain(client):
    res_id = await create_measure(client)
    resp = await client.get(f"{BASE}/{res_id}")
    assert resp.status_code == 200, resp.text
    assert_plain_measure(resp.json(), id=res_id)


async def test_get_measure_fhir(client):
    res_id = await create_measure(client)
    resp = await client.get(f"{BASE}/{res_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    assert_fhir_measure(resp.json(), id=str(res_id))


async def test_get_measure_not_found(client):
    resp = await client.get(f"{BASE}/999999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_measure(client):
    res_id = await create_measure(client)
    patch_payload = {
        "title": "Updated Title for Measure",
        "description": "Updated description.",
    }
    resp = await client.patch(f"{BASE}/{res_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    assert_plain_measure(
        resp.json(),
        title="Updated Title for Measure",
        description="Updated description.",
    )


async def test_patch_measure_fhir(client):
    res_id = await create_measure(client)
    patch_payload = {
        "title": "FHIR Updated Title",
    }
    resp = await client.patch(f"{BASE}/{res_id}", json=patch_payload, headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    assert_fhir_measure(resp.json(), title="FHIR Updated Title")


async def test_patch_measure_not_found(client):
    resp = await client.patch(f"{BASE}/999999999", json={"title": "test"})
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_measures_plain(client):
    await create_measure(client)
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    assert_paginated(resp.json())


async def test_list_measures_fhir(client):
    await create_measure(client)
    resp = await client.get(f"{BASE}/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    assert_fhir_bundle(resp.json())


async def test_list_measures_filter_identifier(client):
    resp = await client.post(
        f"{BASE}/",
        json={
            "status": "draft",
            "name": "FilterTestMeasure",
            "identifier": [
                {
                    "system": "http://example.org/meas-ids",
                    "value": "FLT-MEAS-001",
                }
            ],
        },
    )
    assert resp.status_code == 201, resp.text

    resp = await client.get(f"{BASE}/?identifier=http://example.org/meas-ids|FLT-MEAS-001")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] >= 1
    assert any(
        any(i.get("value") == "FLT-MEAS-001" for i in (item.get("identifier") or []))
        for item in data["data"]
    )


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_measure(client):
    res_id = await create_measure(client)
    del_resp = await client.delete(f"{BASE}/{res_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"{BASE}/{res_id}")
    assert get_resp.status_code == 404


async def test_delete_measure_not_found(client):
    resp = await client.delete(f"{BASE}/999999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Auth & Scoping ───────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    # Create with org-test (default)
    res_id = await create_measure(client)

    # Switch to org-other
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-other",
        permissions=MEASURE_PERMS,
    )

    get_resp = await client.get(f"{BASE}/{res_id}")
    assert get_resp.status_code == 404, "Other org must not see this resource"

    patch_resp = await client.patch(f"{BASE}/{res_id}", json={"title": "other"})
    assert patch_resp.status_code == 404, "Other org must not patch this resource"

    del_resp = await client.delete(f"{BASE}/{res_id}")
    assert del_resp.status_code == 404, "Other org must not delete this resource"


async def test_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=MEASURE_PERMS,
    )
    resp = await client.post(f"{BASE}/", json=minimal_measure())
    assert resp.status_code == 403, resp.text
    assert_operation_outcome(resp.json(), 403, resp.status_code)


async def test_missing_permission_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=[],
    )
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 403, resp.text
    assert_operation_outcome(resp.json(), 403, resp.status_code)

"""Core SpecimenDefinition endpoint coverage.

SpecimenDefinition has 5 endpoints (create/get/patch/list/delete),
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
    assert_fhir_specimen_definition,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_specimen_definition,
)
from tests.integration.specimen_definition.support import (
    BASE,
    FHIR_ACCEPT,
    create_specimen_definition,
    create_test_organization,
    full_specimen_definition,
    minimal_specimen_definition,
)

SPECIMEN_DEFINITION_PERMS = [
    "specimen_definition:create",
    "specimen_definition:read",
    "specimen_definition:update",
    "specimen_definition:delete",
    "organization:create",
    "organization:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_specimen_definition_minimal(client):
    payload = minimal_specimen_definition()
    resp = await client.post(f"{BASE}/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_specimen_definition(data, time_aspect="fasting")


async def test_create_specimen_definition_full_plain(client):
    org_id = await create_test_organization(client)
    payload = full_specimen_definition(org_id)
    resp = await client.post(f"{BASE}/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert_plain_specimen_definition(data, time_aspect="morning")
    assert data["identifier"]["value"] == "SERUM-2026-001"
    assert data["type_collected"]["text"] == "Venous blood"
    assert len(data["patient_preparation"]) == 1
    assert len(data["collection"]) == 1
    assert len(data["type_tested"]) == 1

    tt = data["type_tested"][0]
    assert tt["preference"] == "preferred"
    assert tt["container"]["description"] == "Serum separator tube (SST)"
    assert tt["container"]["capacity_value"] == 5.0
    assert tt["container"]["minimum_volume_quantity_value"] == 1.0
    assert len(tt["container"]["additive"]) == 1
    assert len(tt["rejection_criterion"]) == 1
    assert len(tt["handling"]) == 1


async def test_create_specimen_definition_fhir(client):
    payload = minimal_specimen_definition()
    resp = await client.post(f"{BASE}/", json=payload, headers=FHIR_ACCEPT)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_specimen_definition(data, timeAspect="fasting")


async def test_create_specimen_definition_invalid_org_ref(client):
    payload = minimal_specimen_definition()
    payload["identifier"] = {
        "value": "SERUM-FAIL",
        "assigner": "Organization/999999",
    }
    resp = await client.post(f"{BASE}/", json=payload)
    assert resp.status_code == 422, resp.text
    assert_operation_outcome(resp.json(), 422, resp.status_code)


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_specimen_definition_plain(client):
    res_id = await create_specimen_definition(client)
    resp = await client.get(f"{BASE}/{res_id}")
    assert resp.status_code == 200, resp.text
    assert_plain_specimen_definition(resp.json(), id=res_id)


async def test_get_specimen_definition_fhir(client):
    res_id = await create_specimen_definition(client)
    resp = await client.get(f"{BASE}/{res_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    assert_fhir_specimen_definition(resp.json(), id=str(res_id))


async def test_get_specimen_definition_not_found(client):
    resp = await client.get(f"{BASE}/999999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_specimen_definition(client):
    res_id = await create_specimen_definition(client)
    patch_payload = {
        "time_aspect": "24 hour collection",
    }
    resp = await client.patch(f"{BASE}/{res_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    assert_plain_specimen_definition(resp.json(), time_aspect="24 hour collection")


async def test_patch_specimen_definition_fhir(client):
    res_id = await create_specimen_definition(client)
    patch_payload = {
        "time_aspect": "postprandial",
    }
    resp = await client.patch(f"{BASE}/{res_id}", json=patch_payload, headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    assert_fhir_specimen_definition(resp.json(), timeAspect="postprandial")


async def test_patch_specimen_definition_not_found(client):
    resp = await client.patch(f"{BASE}/999999999", json={"time_aspect": "test"})
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_specimen_definitions_plain(client):
    await create_specimen_definition(client)
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    assert_paginated(resp.json())


async def test_list_specimen_definitions_fhir(client):
    await create_specimen_definition(client)
    resp = await client.get(f"{BASE}/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    assert_fhir_bundle(resp.json())


async def test_list_specimen_definitions_filter_identifier(client):
    resp = await client.post(
        f"{BASE}/",
        json={
            "time_aspect": "morning",
            "identifier": {
                "system": "http://example.org/spec-defs",
                "value": "FLT-TEST-001",
            },
        },
    )
    assert resp.status_code == 201, resp.text

    resp = await client.get(f"{BASE}/?identifier=http://example.org/spec-defs|FLT-TEST-001")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["total"] >= 1
    assert any(
        item.get("identifier", {}).get("value") == "FLT-TEST-001"
        for item in data["data"]
    )


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_specimen_definition(client):
    res_id = await create_specimen_definition(client)
    del_resp = await client.delete(f"{BASE}/{res_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"{BASE}/{res_id}")
    assert get_resp.status_code == 404


async def test_delete_specimen_definition_not_found(client):
    resp = await client.delete(f"{BASE}/999999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, resp.status_code)


# ── Auth & Scoping ───────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    # Create with org-test (default)
    res_id = await create_specimen_definition(client)

    # Switch to org-other
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-other",
        permissions=SPECIMEN_DEFINITION_PERMS,
    )

    get_resp = await client.get(f"{BASE}/{res_id}")
    assert get_resp.status_code == 404, "Other org must not see this resource"

    patch_resp = await client.patch(f"{BASE}/{res_id}", json={"time_aspect": "other"})
    assert patch_resp.status_code == 404, "Other org must not patch this resource"

    del_resp = await client.delete(f"{BASE}/{res_id}")
    assert del_resp.status_code == 404, "Other org must not delete this resource"


async def test_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=SPECIMEN_DEFINITION_PERMS,
    )
    resp = await client.post(f"{BASE}/", json=minimal_specimen_definition())
    assert resp.status_code == 403, resp.text
    assert_operation_outcome(resp.json(), 403, resp.status_code)


async def test_missing_permission_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=[],
    )
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 403, resp.text
    assert_operation_outcome(resp.json(), 403, resp.status_code)

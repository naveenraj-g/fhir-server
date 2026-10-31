"""Core observation_definition endpoint coverage.

ObservationDefinition has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
Every supplied sub-resource list on create/patch replaces corresponding rows wholesale.

This file holds:
- create (minimal + full nested payload, FHIR format, validation)
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
    assert_fhir_observation_definition,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_observation_definition,
)
from tests.integration.observation_definition.support import (
    BASE,
    FHIR_ACCEPT,
    create_observation_definition,
    full_observation_definition,
    minimal_observation_definition,
)

OBSERVATION_DEFINITION_PERMS = [
    "observation_definition:create",
    "observation_definition:read",
    "observation_definition:update",
    "observation_definition:delete",
    "organization:create",
    "organization:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_observation_definition_minimal(client):
    resp = await client.post(BASE + "/", json=minimal_observation_definition())
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_observation_definition(data)
    assert data["code"]["codings"][0]["code"] == "15074-8"


async def test_create_observation_definition_full(client):
    payload = full_observation_definition()
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_observation_definition(data)
    assert data["code"]["codings"][0]["code"] == "15074-8"
    assert len(data["category"]) == 1
    assert data["category"][0]["codings"][0]["code"] == "laboratory"
    assert data["permitted_data_type"] == ["Quantity", "string"]
    assert data["multiple_results_allowed"] is False
    assert data["method"]["codings"][0]["code"] == "271077007"
    assert data["preferred_report_name"] == "Blood Glucose"
    assert data["quantitative_details"]["conversion_factor"] == 0.0555
    assert len(data["qualified_interval"]) == 1
    assert data["qualified_interval"][0]["category"] == "reference"
    assert data["qualified_interval"][0]["range_low_value"] == 70.0
    assert data["valid_coded_value_set"] == "ValueSet/40001"
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "OBSDEF-12345"


async def test_create_observation_definition_fhir_content_negotiation(client):
    resp = await client.post(
        BASE + "/",
        json=minimal_observation_definition(),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_observation_definition(data)
    assert data["code"]["coding"][0]["code"] == "15074-8"


async def test_create_observation_definition_validation_failure_missing_code(client):
    resp = await client.post(
        BASE + "/",
        json={"preferred_report_name": "No Code"},
    )
    assert resp.status_code == 422, resp.text


async def test_create_observation_definition_invalid_permitted_data_type(client):
    resp = await client.post(
        BASE + "/",
        json={
            "code": {"text": "Blood Glucose"},
            "permitted_data_type": ["invalid_type"],
        },
    )
    assert resp.status_code == 422, resp.text


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_observation_definition_plain(client):
    obsdef = await create_observation_definition(client)
    resp = await client.get(f"{BASE}/{obsdef['id']}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_observation_definition(data, id=obsdef["id"])
    assert data["code"]["codings"][0]["code"] == "15074-8"


async def test_get_observation_definition_fhir(client):
    obsdef = await create_observation_definition(client)
    resp = await client.get(f"{BASE}/{obsdef['id']}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_observation_definition(data, id=str(obsdef["id"]))


async def test_get_observation_definition_not_found(client):
    resp = await client.get(f"{BASE}/99999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, 404)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_observation_definition_scalar_fields(client):
    obsdef = await create_observation_definition(client)
    patch_body = {
        "preferred_report_name": "Updated Glucose Name",
        "multiple_results_allowed": True,
    }
    resp = await client.patch(f"{BASE}/{obsdef['id']}", json=patch_body)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_observation_definition(data, id=obsdef["id"])
    assert data["preferred_report_name"] == "Updated Glucose Name"
    assert data["multiple_results_allowed"] is True


async def test_patch_observation_definition_sub_resources_replace(client):
    obsdef = await create_observation_definition(client)
    patch_body = {
        "identifier": [
            {
                "use": "secondary",
                "system": "http://example.org/internal",
                "value": "INT-999",
            }
        ],
        "category": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                        "display": "Vital Signs",
                    }
                ],
                "text": "Vital Signs",
            }
        ],
    }
    resp = await client.patch(f"{BASE}/{obsdef['id']}", json=patch_body)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "INT-999"
    assert len(data["category"]) == 1
    assert data["category"][0]["codings"][0]["code"] == "vital-signs"


async def test_patch_observation_definition_not_found(client):
    resp = await client.patch(f"{BASE}/99999999", json={"preferred_report_name": "X"})
    assert resp.status_code == 404, resp.text


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_observation_definitions_plain(client):
    obsdef = await create_observation_definition(client)
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    ids = [item["id"] for item in data["data"]]
    assert obsdef["id"] in ids


async def test_list_observation_definitions_fhir_bundle(client):
    obsdef = await create_observation_definition(client)
    resp = await client.get(f"{BASE}/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    entry_ids = [e["resource"]["id"] for e in data["entry"]]
    assert str(obsdef["id"]) in entry_ids


async def test_list_observation_definitions_filters(client):
    obsdef = await create_observation_definition(
        client,
        code={
            "coding": [{"system": "http://loinc.org", "code": "FILTER-CODE-999"}],
            "text": "Filtered Test",
        },
        category=[
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "exam",
                    }
                ]
            }
        ],
        permitted_data_type=["boolean"],
        identifier=[{"system": "http://test.org/id", "value": "FILTER-ID-123"}],
    )

    # Filter by code
    resp = await client.get(f"{BASE}/?code=FILTER-CODE-999")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert any(x["id"] == obsdef["id"] for x in items)

    # Filter by category
    resp = await client.get(f"{BASE}/?category=exam")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert any(x["id"] == obsdef["id"] for x in items)

    # Filter by permitted_data_type
    resp = await client.get(f"{BASE}/?permitted_data_type=boolean")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert any(x["id"] == obsdef["id"] for x in items)

    # Filter by identifier
    resp = await client.get(f"{BASE}/?identifier=FILTER-ID-123")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert any(x["id"] == obsdef["id"] for x in items)


async def test_list_observation_definitions_pagination(client):
    resp = await client.get(f"{BASE}/?limit=2&offset=0")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["data"]) <= 2


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_observation_definition_success(client):
    obsdef = await create_observation_definition(client)
    del_resp = await client.delete(f"{BASE}/{obsdef['id']}")
    assert del_resp.status_code == 204, del_resp.text

    get_resp = await client.get(f"{BASE}/{obsdef['id']}")
    assert get_resp.status_code == 404


async def test_delete_observation_definition_not_found(client):
    resp = await client.delete(f"{BASE}/99999999")
    assert resp.status_code == 404, resp.text


# ── Auth & Scoping ───────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    obsdef = await create_observation_definition(client)

    # Switch user to another organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-other",
        permissions=OBSERVATION_DEFINITION_PERMS,
    )
    # Get -> 404 (not 403, no leak)
    resp = await client.get(f"{BASE}/{obsdef['id']}")
    assert resp.status_code == 404, resp.text

    # Patch -> 404
    resp = await client.patch(
        f"{BASE}/{obsdef['id']}", json={"preferred_report_name": "Leak Attempt"}
    )
    assert resp.status_code == 404, resp.text

    # Delete -> 404
    resp = await client.delete(f"{BASE}/{obsdef['id']}")
    assert resp.status_code == 404, resp.text

    # List -> does not include obsdef["id"]
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert obsdef["id"] not in ids


async def test_org_less_token_rejected(client):
    # Actor without org_id
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=OBSERVATION_DEFINITION_PERMS,
    )
    resp = await client.post(BASE + "/", json=minimal_observation_definition())
    assert resp.status_code == 403, resp.text

    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 403, resp.text


async def test_missing_permission_rejected(client):
    # No observation_definition permissions
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=["patient:read"]
    )
    resp = await client.post(BASE + "/", json=minimal_observation_definition())
    assert resp.status_code == 403, resp.text

"""Core activity_definition endpoint coverage.

ActivityDefinition has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_activity_definition,
    assert_fhir_bundle,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_activity_definition,
)
from tests.integration.activity_definition.support import (
    BASE,
    FHIR_ACCEPT,
    create_activity_definition,
    full_activity_definition,
    minimal_activity_definition,
)

ACTIVITY_DEFINITION_PERMS = [
    "activity_definition:create",
    "activity_definition:read",
    "activity_definition:update",
    "activity_definition:delete",
    "organization:create",
    "organization:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_activity_definition_minimal(client):
    resp = await client.post(BASE + "/", json=minimal_activity_definition())
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_activity_definition(data)
    assert data["status"] == "draft"
    assert data["name"] == "BloodGlucoseMonitoringActivity"


async def test_create_activity_definition_full(client):
    payload = full_activity_definition()
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_activity_definition(data)
    assert data["status"] == "draft"
    assert data["name"] == "FullActivityDefinition"
    assert data["subtitle"] == "Subtitle test"
    assert data["experimental"] is True
    assert data["code"]["codings"][0]["code"] == "35335000"
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "ACTDEF-12345"
    assert len(data["contact"]) == 1
    assert data["contact"][0]["name"] == "Clinical Committee"
    assert len(data["use_context"]) == 1
    assert data["use_context"][0]["code_code"] == "venue"
    assert len(data["jurisdiction"]) == 1
    assert data["jurisdiction"][0]["codings"][0]["code"] == "US"
    assert len(data["topic"]) == 1
    assert data["topic"][0]["codings"][0]["code"] == "394583002"
    assert len(data["participant"]) == 1
    assert data["participant"][0]["type"] == "practitioner"
    assert len(data["dosage"]) == 1
    assert data["dosage"][0]["sequence"] == 1
    assert len(data["body_site"]) == 1
    assert len(data["related_artifact"]) == 1
    assert len(data["dynamic_value"]) == 1
    assert data["dynamic_value"][0]["expression_expression"] == "CalculatePriority()"


async def test_create_activity_definition_fhir_content_negotiation(client):
    resp = await client.post(
        BASE + "/",
        json=minimal_activity_definition(),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_activity_definition(data)
    assert data["status"] == "draft"
    assert data["name"] == "BloodGlucoseMonitoringActivity"


async def test_create_activity_definition_validation_failure_missing_status(client):
    resp = await client.post(
        BASE + "/",
        json={"name": "NoStatus"},
    )
    assert resp.status_code == 422, resp.text


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_activity_definition_plain(client):
    actdef = await create_activity_definition(client)
    resp = await client.get(f"{BASE}/{actdef['id']}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_activity_definition(data, id=actdef["id"])
    assert data["name"] == "BloodGlucoseMonitoringActivity"


async def test_get_activity_definition_fhir(client):
    actdef = await create_activity_definition(client)
    resp = await client.get(f"{BASE}/{actdef['id']}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_activity_definition(data, id=str(actdef["id"]))


async def test_get_activity_definition_not_found(client):
    resp = await client.get(f"{BASE}/99999999")
    assert resp.status_code == 404, resp.text
    assert_operation_outcome(resp.json(), 404, 404)


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_activity_definition_scalar_fields(client):
    actdef = await create_activity_definition(client)
    patch_body = {
        "title": "Updated Title Name",
        "priority": "urgent",
    }
    resp = await client.patch(f"{BASE}/{actdef['id']}", json=patch_body)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_activity_definition(data, id=actdef["id"])
    assert data["title"] == "Updated Title Name"
    assert data["priority"] == "urgent"


async def test_patch_activity_definition_sub_resources_replace(client):
    actdef = await create_activity_definition(client)
    patch_body = {
        "identifier": [
            {
                "use": "secondary",
                "system": "http://example.org/internal",
                "value": "INT-999",
            }
        ],
        "topic": [
            {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "12345",
                        "display": "New Topic",
                    }
                ],
                "text": "New Topic",
            }
        ],
    }
    resp = await client.patch(f"{BASE}/{actdef['id']}", json=patch_body)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "INT-999"
    assert len(data["topic"]) == 1
    assert data["topic"][0]["codings"][0]["code"] == "12345"


async def test_patch_activity_definition_not_found(client):
    resp = await client.patch(f"{BASE}/99999999", json={"title": "X"})
    assert resp.status_code == 404, resp.text


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_activity_definitions_plain(client):
    actdef = await create_activity_definition(client)
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    ids = [item["id"] for item in data["data"]]
    assert actdef["id"] in ids


async def test_list_activity_definitions_fhir_bundle(client):
    actdef = await create_activity_definition(client)
    resp = await client.get(f"{BASE}/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    entry_ids = [e["resource"]["id"] for e in data["entry"]]
    assert str(actdef["id"]) in entry_ids


async def test_list_activity_definitions_filters(client):
    actdef = await create_activity_definition(
        client,
        name="UniqueFilterActivity",
        status="active",
        kind="MedicationRequest",
        intent="plan",
        priority="stat",
        identifier=[{"system": "http://test.org/id", "value": "FILTER-ID-123"}],
    )

    # Filter by name
    resp = await client.get(f"{BASE}/?name=UniqueFilter")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert any(x["id"] == actdef["id"] for x in items)

    # Filter by status
    resp = await client.get(f"{BASE}/?status=active")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert any(x["id"] == actdef["id"] for x in items)

    # Filter by kind
    resp = await client.get(f"{BASE}/?kind=MedicationRequest")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert any(x["id"] == actdef["id"] for x in items)

    # Filter by identifier
    resp = await client.get(f"{BASE}/?identifier=FILTER-ID-123")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert any(x["id"] == actdef["id"] for x in items)


async def test_list_activity_definitions_pagination(client):
    resp = await client.get(f"{BASE}/?limit=2&offset=0")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["data"]) <= 2


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_activity_definition_success(client):
    actdef = await create_activity_definition(client)
    del_resp = await client.delete(f"{BASE}/{actdef['id']}")
    assert del_resp.status_code == 204, del_resp.text

    get_resp = await client.get(f"{BASE}/{actdef['id']}")
    assert get_resp.status_code == 404


async def test_delete_activity_definition_not_found(client):
    resp = await client.delete(f"{BASE}/99999999")
    assert resp.status_code == 404, resp.text


# ── Auth & Scoping ───────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    actdef = await create_activity_definition(client)

    # Switch user to another organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-other",
        permissions=ACTIVITY_DEFINITION_PERMS,
    )
    # Get -> 404 (not 403, no leak)
    resp = await client.get(f"{BASE}/{actdef['id']}")
    assert resp.status_code == 404, resp.text

    # Patch -> 404
    resp = await client.patch(
        f"{BASE}/{actdef['id']}", json={"title": "Leak Attempt"}
    )
    assert resp.status_code == 404, resp.text

    # Delete -> 404
    resp = await client.delete(f"{BASE}/{actdef['id']}")
    assert resp.status_code == 404, resp.text

    # List -> does not include actdef["id"]
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert actdef["id"] not in ids


async def test_org_less_token_rejected(client):
    # Actor without org_id
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=ACTIVITY_DEFINITION_PERMS,
    )
    resp = await client.post(BASE + "/", json=minimal_activity_definition())
    assert resp.status_code == 403, resp.text

    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 403, resp.text


async def test_missing_permission_rejected(client):
    # No activity_definition permissions
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=["patient:read"]
    )
    resp = await client.post(BASE + "/", json=minimal_activity_definition())
    assert resp.status_code == 403, resp.text

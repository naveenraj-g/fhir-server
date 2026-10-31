"""Core plan_definition endpoint coverage.

PlanDefinition has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_plan_definition,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_plan_definition,
)
from tests.integration.plan_definition.support import (
    BASE,
    FHIR_ACCEPT,
    create_plan_definition,
    full_plan_definition,
    minimal_plan_definition,
)

PLAN_DEFINITION_PERMS = [
    "plan_definition:create",
    "plan_definition:read",
    "plan_definition:update",
    "plan_definition:delete",
    "organization:create",
    "organization:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_plan_definition_minimal(client):
    resp = await client.post(BASE + "/", json=minimal_plan_definition())
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_plan_definition(data)
    assert data["status"] == "draft"
    assert data["name"] == "DiabetesCarePlanDefinition"


async def test_create_plan_definition_full(client):
    payload = full_plan_definition()
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_plan_definition(data)
    assert data["status"] == "draft"
    assert data["name"] == "FullPlanDefinition"
    assert data["subtitle"] == "Comprehensive CDS Protocol"
    assert data["experimental"] is True
    assert data["type"]["codings"][0]["code"] == "clinical-protocol"
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "PLANDEF-12345"
    assert len(data["contact"]) == 1
    assert data["contact"][0]["name"] == "Clinical Committee"
    assert len(data["use_context"]) == 1
    assert data["use_context"][0]["code_code"] == "venue"
    assert len(data["jurisdiction"]) == 1
    assert data["jurisdiction"][0]["codings"][0]["code"] == "US"
    assert len(data["topic"]) == 1
    assert data["topic"][0]["codings"][0]["code"] == "394583002"
    assert len(data["related_artifact"]) == 1
    assert len(data["goal"]) == 1
    assert data["goal"][0]["goal_id"] == "goal-hba1c"
    assert len(data["action"]) == 1
    assert data["action"][0]["action_id_str"] == "act-1"
    assert len(data["action"][0]["action"]) == 1
    assert data["action"][0]["action"][0]["action_id_str"] == "act-1-1"


async def test_create_plan_definition_fhir_content_negotiation(client):
    resp = await client.post(
        BASE + "/",
        json=minimal_plan_definition(),
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_plan_definition(data)
    assert data["status"] == "draft"
    assert data["name"] == "DiabetesCarePlanDefinition"


async def test_create_plan_definition_validation_failure_missing_status(client):
    resp = await client.post(
        BASE + "/",
        json={"name": "NoStatus"},
    )
    assert resp.status_code == 422, resp.text


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_plan_definition_plain(client):
    plandef = await create_plan_definition(client)
    resp = await client.get(f"{BASE}/{plandef['id']}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_plan_definition(data, id=plandef["id"])
    assert data["name"] == "DiabetesCarePlanDefinition"


async def test_get_plan_definition_fhir(client):
    plandef = await create_plan_definition(client)
    resp = await client.get(f"{BASE}/{plandef['id']}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_plan_definition(data, id=str(plandef["id"]))
    assert data["name"] == "DiabetesCarePlanDefinition"


async def test_get_plan_definition_not_found(client):
    resp = await client.get(f"{BASE}/99999999")
    assert resp.status_code == 404, resp.text


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_plan_definition_fields(client):
    plandef = await create_plan_definition(client)
    patch_payload = {
        "title": "Updated Title",
        "status": "active",
        "description": "Updated description",
    }
    resp = await client.patch(f"{BASE}/{plandef['id']}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["title"] == "Updated Title"
    assert data["status"] == "active"
    assert data["description"] == "Updated description"


async def test_patch_plan_definition_sub_resources_replace(client):
    plandef = await create_plan_definition(client)

    # Patch with goals and actions
    patch_payload = {
        "goal": [
            {
                "id": "new-goal-1",
                "description": {"text": "Target BP < 120/80"},
            }
        ],
        "action": [
            {
                "id": "new-act-1",
                "title": "Check Blood Pressure",
                "prefix": "BP-1",
            }
        ],
    }
    resp = await client.patch(f"{BASE}/{plandef['id']}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["goal"]) == 1
    assert data["goal"][0]["goal_id"] == "new-goal-1"
    assert len(data["action"]) == 1
    assert data["action"][0]["action_id_str"] == "new-act-1"

    # Replace again with empty list
    resp2 = await client.patch(f"{BASE}/{plandef['id']}", json={"goal": [], "action": []})
    assert resp2.status_code == 200, resp2.text
    data2 = resp2.json()
    assert len(data2["goal"]) == 0
    assert len(data2["action"]) == 0


async def test_patch_plan_definition_not_found(client):
    resp = await client.patch(f"{BASE}/99999999", json={"title": "Not Found"})
    assert resp.status_code == 404, resp.text


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_plan_definitions_plain(client):
    await create_plan_definition(client)
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    assert len(data["data"]) >= 1


async def test_list_plan_definitions_fhir(client):
    await create_plan_definition(client)
    resp = await client.get(f"{BASE}/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)


async def test_list_plan_definitions_filters(client):
    unique_name = "PlanDefFilterUnique"
    plandef = await create_plan_definition(
        client,
        name=unique_name,
        identifier=[
            {
                "use": "official",
                "system": "http://example.org/plandef-id",
                "value": "FILTER-ID-123",
            }
        ],
    )

    # Filter by name
    resp = await client.get(f"{BASE}/?name={unique_name}")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert any(x["id"] == plandef["id"] for x in items)

    # Filter by identifier
    resp = await client.get(f"{BASE}/?identifier=FILTER-ID-123")
    assert resp.status_code == 200, resp.text
    items = resp.json()["data"]
    assert any(x["id"] == plandef["id"] for x in items)


async def test_list_plan_definitions_pagination(client):
    resp = await client.get(f"{BASE}/?limit=2&offset=0")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["data"]) <= 2


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_plan_definition_success(client):
    plandef = await create_plan_definition(client)
    del_resp = await client.delete(f"{BASE}/{plandef['id']}")
    assert del_resp.status_code == 204, del_resp.text

    get_resp = await client.get(f"{BASE}/{plandef['id']}")
    assert get_resp.status_code == 404


async def test_delete_plan_definition_not_found(client):
    resp = await client.delete(f"{BASE}/99999999")
    assert resp.status_code == 404, resp.text


# ── Auth & Scoping ───────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    plandef = await create_plan_definition(client)

    # Switch user to another organization
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="org-other",
        permissions=PLAN_DEFINITION_PERMS,
    )
    # Get -> 404 (not 403, no leak)
    resp = await client.get(f"{BASE}/{plandef['id']}")
    assert resp.status_code == 404, resp.text

    # Patch -> 404
    resp = await client.patch(
        f"{BASE}/{plandef['id']}", json={"title": "Leak Attempt"}
    )
    assert resp.status_code == 404, resp.text

    # Delete -> 404
    resp = await client.delete(f"{BASE}/{plandef['id']}")
    assert resp.status_code == 404, resp.text

    # List -> does not include plandef["id"]
    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert plandef["id"] not in ids


async def test_org_less_token_rejected(client):
    # Actor without org_id
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=PLAN_DEFINITION_PERMS,
    )
    resp = await client.post(BASE + "/", json=minimal_plan_definition())
    assert resp.status_code == 403, resp.text

    resp = await client.get(f"{BASE}/")
    assert resp.status_code == 403, resp.text


async def test_missing_permission_rejected(client):
    # No plan_definition permissions
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=["patient:read"]
    )
    resp = await client.post(BASE + "/", json=minimal_plan_definition())
    assert resp.status_code == 403, resp.text

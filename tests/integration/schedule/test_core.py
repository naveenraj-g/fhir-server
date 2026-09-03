"""Core schedule endpoint coverage.

Schedule follows Organization/HealthcareService's "set once, rarely edited"
shape — 5 endpoints (create/get/patch/list/delete), no sub-resource routes
and no /me route. Every supplied sub-resource list on create/patch
(identifier, serviceCategory, serviceType, specialty) replaces the
corresponding rows wholesale; `actor` is required (1..*) and may also be
replaced but never emptied. Same JWT/RBAC auth rollout as HealthcareService:
org_id/created_by/updated_by come from the verified token, never the body,
and Schedule has no user_id at all.

This file holds:
- create (minimal + full nested payload, FHIR format, validation,
  actor reference resolution + rejection, Device actor with no check)
- read (plain + FHIR, not found)
- list (plain, FHIR bundle, pagination, every Medplum-mirrored filter, sort)
- patch (field updates, sub-resource list replace, actor-cannot-be-emptied,
  not found)
- delete
- auth: org-less token, missing permission scope, cross-org isolation
"""

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import (
    assert_fhir_bundle,
    assert_fhir_schedule,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_schedule,
)
from tests.integration.schedule.support import (
    BASE,
    FHIR_ACCEPT,
    FULL,
    MINIMAL,
    create_schedule,
    seed_practitioner,
)

SCHED_PERMS = [
    "schedule:create",
    "schedule:read",
    "schedule:update",
    "schedule:delete",
]


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_schedule_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200
    assert_plain_schedule(resp.json(), active=True)


async def test_create_schedule_full(client):
    resp = await client.post(BASE + "/", json=FULL)
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_schedule(data, active=True, comment="Available for urgent bookings only.")
    assert data["identifier"][0]["value"] == "SCHED-1001"
    assert data["identifier"][0]["assigner_identifier_value"] == "EXTERNAL-1"
    assert data["service_category"][0]["coding_code"] == "17"
    assert data["service_type"][0]["coding_code"] == "57"
    assert data["specialty"][0]["coding_code"] == "394814009"
    assert data["actor"][0]["reference_identifier_value"] == "ACTOR-9"
    assert data["planning_horizon_start"] is not None
    assert data["planning_horizon_end"] is not None


async def test_create_schedule_returns_fhir_format(client):
    resp = await client.post(BASE + "/", json=MINIMAL, headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert "application/fhir+json" in resp.headers["content-type"]
    assert_fhir_schedule(resp.json())


async def test_create_schedule_extra_field_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "nonexistent_field": "value"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_schedule_org_id_in_body_rejected(client):
    """org_id/created_by/updated_by come from the verified token — not
    request-body fields — since Schedule's JWT/RBAC rollout."""
    resp = await client.post(BASE + "/", json={**MINIMAL, "org_id": "sneaky-org"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_schedule_missing_actor_rejected(client):
    """Schedule.actor is 1..* — required on create."""
    payload = {k: v for k, v in MINIMAL.items() if k != "actor"}
    resp = await client.post(BASE + "/", json=payload)
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_schedule_empty_actor_list_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "actor": []})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_schedule_created_by_derived_from_actor(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200
    data = resp.json()
    assert data["created_by"] == "u-test"
    assert data["org_id"] == "org-test"


async def test_create_schedule_with_resolved_practitioner_actor(client, _engine):
    """actor[] is a real cross-resource reference validated for existence at
    write time. Practitioner's own router isn't mounted in this test env, so
    seed a row directly."""
    practitioner_id = await seed_practitioner(_engine)
    resp = await client.post(
        BASE + "/",
        json={
            **MINIMAL,
            "actor": [{"reference": f"Practitioner/{practitioner_id}"}],
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["actor"][0]["reference_id"] == practitioner_id
    assert data["actor"][0]["reference"] == f"Practitioner/{practitioner_id}"


async def test_create_schedule_nonexistent_actor_rejected(client):
    resp = await client.post(
        BASE + "/",
        json={**MINIMAL, "actor": [{"reference": "Practitioner/9999999"}]},
    )
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_schedule_device_actor_no_existence_check(client):
    """Device isn't a modeled resource in this system, so a Device-typed
    actor reference is accepted with no existence check — same treatment
    HealthcareService gives its unmodeled Endpoint target."""
    resp = await client.post(
        BASE + "/",
        json={
            **MINIMAL,
            "actor": [
                {"reference": "Device/12345", "reference_display": "Infusion pump"}
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["actor"][0]["reference_type"] == "Device"
    assert data["actor"][0]["reference_id"] == 12345


# ── Get ──────────────────────────────────────────────────────────────────────


async def test_get_schedule_by_id_plain(client):
    sched_id = await create_schedule(client)
    resp = await client.get(f"{BASE}/{sched_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_schedule(data, active=True)
    assert data["id"] == sched_id


async def test_get_schedule_by_id_fhir(client):
    sched_id = await create_schedule(client)
    resp = await client.get(f"{BASE}/{sched_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert_fhir_schedule(resp.json())
    assert resp.json()["id"] == str(sched_id)


async def test_get_schedule_not_found(client):
    resp = await client.get(f"{BASE}/9999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────────


async def test_list_schedules_plain(client):
    await create_schedule(client)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200
    assert_paginated(resp.json())


async def test_list_schedules_fhir_bundle(client):
    await create_schedule(client)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert_fhir_bundle(resp.json())


async def test_list_schedules_pagination(client):
    for _ in range(3):
        await create_schedule(client)
    resp = await client.get(f"{BASE}/?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) <= 2
    assert data["limit"] == 2


async def test_list_schedules_filter_active(client):
    await create_schedule(client, {**MINIMAL, "active": True})
    await create_schedule(client, {**MINIMAL, "active": False})
    resp = await client.get(BASE + "/", params={"active": "false"})
    assert resp.status_code == 200
    assert all(s["active"] is False for s in resp.json()["data"])


async def test_list_schedules_filter_identifier(client):
    await create_schedule(client, FULL)
    resp = await client.get(BASE + "/", params={"identifier": "SCHED-1001"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_schedules_filter_service_category(client):
    await create_schedule(client, FULL)
    resp = await client.get(BASE + "/", params={"service-category": "17"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_schedules_filter_service_type(client):
    await create_schedule(client, FULL)
    resp = await client.get(BASE + "/", params={"service-type": "57"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_schedules_filter_specialty(client):
    await create_schedule(client, FULL)
    resp = await client.get(BASE + "/", params={"specialty": "394814009"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_schedules_filter_actor(client, _engine):
    practitioner_id = await seed_practitioner(_engine)
    await create_schedule(
        client, {**MINIMAL, "actor": [{"reference": f"Practitioner/{practitioner_id}"}]}
    )
    resp = await client.get(
        BASE + "/", params={"actor": f"Practitioner/{practitioner_id}"}
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_schedules_filter_date(client):
    await create_schedule(client, FULL)
    resp = await client.get(BASE + "/", params={"date": "2024-06-01"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_schedules_filter_date_outside_horizon_excludes(client):
    await create_schedule(client, FULL)
    resp = await client.get(BASE + "/", params={"date": "2030-01-01"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


async def test_list_schedules_sort_and_total_mode_none(client):
    await create_schedule(client)
    resp = await client.get(BASE + "/", params={"sort": "-schedule_id", "total_mode": "none"})
    assert resp.status_code == 200
    assert resp.json()["total"] is None


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_schedule_active(client):
    sched_id = await create_schedule(client)
    resp = await client.patch(f"{BASE}/{sched_id}", json={"active": False})
    assert resp.status_code == 200
    data = resp.json()
    assert data["active"] is False
    assert data["updated_by"] == "u-test"


async def test_patch_schedule_comment(client):
    sched_id = await create_schedule(client)
    resp = await client.patch(f"{BASE}/{sched_id}", json={"comment": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["comment"] == "Updated"


async def test_patch_schedule_replaces_service_category_list(client):
    sched_id = await create_schedule(client, FULL)
    resp = await client.patch(
        f"{BASE}/{sched_id}",
        json={
            "service_category": [
                {"coding_code": "new-cat", "coding_display": "New Category"}
            ]
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["service_category"]) == 1
    assert data["service_category"][0]["coding_code"] == "new-cat"
    # Untouched lists are left alone.
    assert len(data["identifier"]) == 1


async def test_patch_schedule_replaces_actor_list(client):
    sched_id = await create_schedule(client, FULL)
    resp = await client.patch(
        f"{BASE}/{sched_id}",
        json={
            "actor": [
                {
                    "reference_identifier_system": "urn:actor-registry",
                    "reference_identifier_value": "ACTOR-REPLACED",
                }
            ]
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["actor"]) == 1
    assert data["actor"][0]["reference_identifier_value"] == "ACTOR-REPLACED"


async def test_patch_schedule_actor_cannot_be_emptied(client):
    sched_id = await create_schedule(client)
    resp = await client.patch(f"{BASE}/{sched_id}", json={"actor": []})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_patch_schedule_not_found(client):
    resp = await client.patch(f"{BASE}/9999999", json={"active": False})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete_schedule(client):
    sched_id = await create_schedule(client)
    resp = await client.delete(f"{BASE}/{sched_id}")
    assert resp.status_code == 204
    assert (await client.get(f"{BASE}/{sched_id}")).status_code == 404


async def test_delete_schedule_not_found(client):
    resp = await client.delete(f"{BASE}/9999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Auth & tenancy ───────────────────────────────────────────────────────────


async def test_create_schedule_no_permission(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=["schedule:read"])
    try:
        resp = await client.post(BASE + "/", json=MINIMAL)
        assert_operation_outcome(resp.json(), expected_status=403, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=SCHED_PERMS)


async def test_create_schedule_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(org_id=None, permissions=SCHED_PERMS)
    try:
        resp = await client.post(BASE + "/", json=MINIMAL)
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=SCHED_PERMS)


async def test_list_schedules_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(org_id=None, permissions=SCHED_PERMS)
    try:
        resp = await client.get(BASE + "/")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=SCHED_PERMS)


async def test_get_schedule_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=SCHED_PERMS)
    sched_id = await create_schedule(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=SCHED_PERMS
    )
    try:
        resp = await other_client.get(f"{BASE}/{sched_id}")
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=SCHED_PERMS)


async def test_patch_schedule_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=SCHED_PERMS)
    sched_id = await create_schedule(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=SCHED_PERMS
    )
    try:
        resp = await other_client.patch(f"{BASE}/{sched_id}", json={"active": False})
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=SCHED_PERMS)


async def test_delete_schedule_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=SCHED_PERMS)
    sched_id = await create_schedule(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=SCHED_PERMS
    )
    try:
        resp = await other_client.delete(f"{BASE}/{sched_id}")
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=SCHED_PERMS)


async def test_list_schedules_cross_tenant_isolation(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=SCHED_PERMS)
    await create_schedule(
        client,
        {
            **MINIMAL,
            "identifier": [{"system": "http://ex.org/tenant-a", "value": "TENANT-A-ONLY"}],
        },
    )
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=SCHED_PERMS
    )
    try:
        resp = await other_client.get(BASE + "/", params={"identifier": "TENANT-A-ONLY"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=SCHED_PERMS)

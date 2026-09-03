"""Core slot endpoint coverage.

Slot follows Organization/HealthcareService/Schedule's "set once, rarely
edited" shape — 5 endpoints (create/get/patch/list/delete), no sub-resource
routes and no /me route. Every supplied sub-resource list on create/patch
(identifier, serviceCategory, serviceType, specialty) replaces the
corresponding rows wholesale. Unlike Schedule.actor (1..*, polymorphic),
Slot.schedule is a single required (1..1) Reference(Schedule) — always
existence-validated, never conditionally. Same JWT/RBAC auth rollout as
Schedule: org_id/created_by/updated_by come from the verified token, never
the body, and Slot has no user_id at all.

This file holds:
- create (minimal + full nested payload, FHIR format, validation, schedule
  reference resolution + rejection, missing/empty schedule rejected)
- read (plain + FHIR, not found)
- list (plain, FHIR bundle, pagination, every Medplum-mirrored filter, sort)
- patch (field updates, sub-resource list replace, not found)
- delete
- auth: org-less token, missing permission scope, cross-org isolation
"""

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import (
    assert_fhir_bundle,
    assert_fhir_slot,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_slot,
)
from tests.integration.slot.support import (
    BASE,
    FHIR_ACCEPT,
    create_schedule,
    create_slot,
    full_slot_payload,
    minimal_slot_payload,
)

SLOT_PERMS = ["slot:create", "slot:read", "slot:update", "slot:delete"]
SLOT_AND_SCHEDULE_PERMS = SLOT_PERMS + ["schedule:create"]


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_slot_minimal(client):
    schedule_id = await create_schedule(client)
    resp = await client.post(BASE + "/", json=minimal_slot_payload(schedule_id))
    assert resp.status_code == 200, resp.text
    assert_plain_slot(resp.json(), status="free")


async def test_create_slot_full(client):
    schedule_id = await create_schedule(client)
    resp = await client.post(BASE + "/", json=full_slot_payload(schedule_id))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_slot(
        data, status="free", comment="Morning slot — first appointment of the day"
    )
    assert data["identifier"][0]["value"] == "SLOT-1001"
    assert data["identifier"][0]["assigner_identifier_value"] == "EXTERNAL-1"
    assert data["service_category"][0]["coding_code"] == "17"
    assert data["service_type"][0]["coding_code"] == "57"
    assert data["specialty"][0]["coding_code"] == "394814009"
    assert data["appointment_type_code"] == "ROUTINE"
    assert data["schedule"] == f"Schedule/{schedule_id}"
    assert data["schedule_display"] == "Dr. Smith's schedule"
    assert data["overbooked"] is False


async def test_create_slot_returns_fhir_format(client):
    schedule_id = await create_schedule(client)
    resp = await client.post(
        BASE + "/", json=minimal_slot_payload(schedule_id), headers=FHIR_ACCEPT
    )
    assert resp.status_code == 200
    assert "application/fhir+json" in resp.headers["content-type"]
    assert_fhir_slot(resp.json())
    data = resp.json()
    assert data["schedule"]["reference"] == f"Schedule/{schedule_id}"
    assert data["status"] == "free"


async def test_create_slot_extra_field_rejected(client):
    schedule_id = await create_schedule(client)
    payload = {**minimal_slot_payload(schedule_id), "nonexistent_field": "value"}
    resp = await client.post(BASE + "/", json=payload)
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_slot_org_id_in_body_rejected(client):
    """org_id/created_by/updated_by come from the verified token — not
    request-body fields — since Slot's JWT/RBAC rollout."""
    schedule_id = await create_schedule(client)
    payload = {**minimal_slot_payload(schedule_id), "org_id": "sneaky-org"}
    resp = await client.post(BASE + "/", json=payload)
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_slot_missing_schedule_rejected(client):
    """Slot.schedule is 1..1 — required on create."""
    payload = {k: v for k, v in minimal_slot_payload(200001).items() if k != "schedule"}
    resp = await client.post(BASE + "/", json=payload)
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_slot_missing_status_rejected(client):
    """Slot.status is 1..1 — required on create."""
    schedule_id = await create_schedule(client)
    payload = {k: v for k, v in minimal_slot_payload(schedule_id).items() if k != "status"}
    resp = await client.post(BASE + "/", json=payload)
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_slot_missing_start_end_rejected(client):
    """Slot.start/end are both 1..1 — required on create."""
    schedule_id = await create_schedule(client)
    payload = {
        k: v
        for k, v in minimal_slot_payload(schedule_id).items()
        if k not in ("start", "end")
    }
    resp = await client.post(BASE + "/", json=payload)
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_slot_created_by_derived_from_actor(client):
    schedule_id = await create_schedule(client)
    resp = await client.post(BASE + "/", json=minimal_slot_payload(schedule_id))
    assert resp.status_code == 200
    data = resp.json()
    assert data["created_by"] == "u-test"
    assert data["org_id"] == "org-test"


async def test_create_slot_with_resolved_schedule(client):
    schedule_id = await create_schedule(client)
    resp = await client.post(BASE + "/", json=minimal_slot_payload(schedule_id))
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["schedule_id"] == schedule_id
    assert data["schedule_type"] == "Schedule"
    assert data["schedule"] == f"Schedule/{schedule_id}"


async def test_create_slot_nonexistent_schedule_rejected(client):
    resp = await client.post(BASE + "/", json=minimal_slot_payload(9999999))
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


# ── Get ──────────────────────────────────────────────────────────────────────


async def test_get_slot_by_id_plain(client):
    slot_id = await create_slot(client)
    resp = await client.get(f"{BASE}/{slot_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_slot(data, status="free")
    assert data["id"] == slot_id


async def test_get_slot_by_id_fhir(client):
    slot_id = await create_slot(client)
    resp = await client.get(f"{BASE}/{slot_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert_fhir_slot(resp.json())
    assert resp.json()["id"] == str(slot_id)


async def test_get_slot_not_found(client):
    resp = await client.get(f"{BASE}/9999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── List ─────────────────────────────────────────────────────────────────────


async def test_list_slots_plain(client):
    await create_slot(client)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200
    assert_paginated(resp.json())


async def test_list_slots_fhir_bundle(client):
    await create_slot(client)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert_fhir_bundle(resp.json())


async def test_list_slots_pagination(client):
    schedule_id = await create_schedule(client)
    for _ in range(3):
        await create_slot(client, schedule_id)
    resp = await client.get(f"{BASE}/?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["data"]) <= 2
    assert data["limit"] == 2


async def test_list_slots_filter_status(client):
    schedule_id = await create_schedule(client)
    await create_slot(client, payload=minimal_slot_payload(schedule_id, status="free"))
    await create_slot(client, payload=minimal_slot_payload(schedule_id, status="busy"))
    resp = await client.get(BASE + "/", params={"status": "busy"})
    assert resp.status_code == 200
    assert all(s["status"] == "busy" for s in resp.json()["data"])


async def test_list_slots_filter_identifier(client):
    schedule_id = await create_schedule(client)
    await create_slot(client, payload=full_slot_payload(schedule_id))
    resp = await client.get(BASE + "/", params={"identifier": "SLOT-1001"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_slots_filter_schedule(client):
    schedule_id = await create_schedule(client)
    await create_slot(client, schedule_id)
    resp = await client.get(BASE + "/", params={"schedule": f"Schedule/{schedule_id}"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_slots_filter_service_category(client):
    schedule_id = await create_schedule(client)
    await create_slot(client, payload=full_slot_payload(schedule_id))
    resp = await client.get(BASE + "/", params={"service-category": "17"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_slots_filter_service_type(client):
    schedule_id = await create_schedule(client)
    await create_slot(client, payload=full_slot_payload(schedule_id))
    resp = await client.get(BASE + "/", params={"service-type": "57"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_slots_filter_specialty(client):
    schedule_id = await create_schedule(client)
    await create_slot(client, payload=full_slot_payload(schedule_id))
    resp = await client.get(BASE + "/", params={"specialty": "394814009"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_slots_filter_appointment_type(client):
    schedule_id = await create_schedule(client)
    await create_slot(client, payload=full_slot_payload(schedule_id))
    resp = await client.get(BASE + "/", params={"appointment-type": "ROUTINE"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_slots_filter_start(client):
    schedule_id = await create_schedule(client)
    await create_slot(client, payload=full_slot_payload(schedule_id))
    resp = await client.get(BASE + "/", params={"start": "ge2024-01-01"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_slots_filter_start_excludes_out_of_range(client):
    schedule_id = await create_schedule(client)
    await create_slot(client, payload=full_slot_payload(schedule_id))
    resp = await client.get(BASE + "/", params={"start": "ge2030-01-01"})
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


async def test_list_slots_filter_end(client):
    schedule_id = await create_schedule(client)
    await create_slot(client, payload=full_slot_payload(schedule_id))
    resp = await client.get(BASE + "/", params={"end": "le2024-12-31"})
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_list_slots_sort_and_total_mode_none(client):
    await create_slot(client)
    resp = await client.get(BASE + "/", params={"sort": "-slot_id", "total_mode": "none"})
    assert resp.status_code == 200
    assert resp.json()["total"] is None


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_slot_status(client):
    slot_id = await create_slot(client)
    resp = await client.patch(f"{BASE}/{slot_id}", json={"status": "busy"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "busy"
    assert data["updated_by"] == "u-test"


async def test_patch_slot_comment(client):
    slot_id = await create_slot(client)
    resp = await client.patch(f"{BASE}/{slot_id}", json={"comment": "Updated"})
    assert resp.status_code == 200
    assert resp.json()["comment"] == "Updated"


async def test_patch_slot_replaces_service_category_list(client):
    schedule_id = await create_schedule(client)
    slot_id = await create_slot(client, payload=full_slot_payload(schedule_id))
    resp = await client.patch(
        f"{BASE}/{slot_id}",
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


async def test_patch_slot_schedule_immutable(client):
    """schedule isn't a field on SlotPatchSchema at all — supplying it is
    rejected by extra='forbid', not silently ignored."""
    slot_id = await create_slot(client)
    resp = await client.patch(f"{BASE}/{slot_id}", json={"schedule": "Schedule/999999"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_patch_slot_not_found(client):
    resp = await client.patch(f"{BASE}/9999999", json={"status": "busy"})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete_slot(client):
    slot_id = await create_slot(client)
    resp = await client.delete(f"{BASE}/{slot_id}")
    assert resp.status_code == 204
    assert (await client.get(f"{BASE}/{slot_id}")).status_code == 404


async def test_delete_slot_not_found(client):
    resp = await client.delete(f"{BASE}/9999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Auth & tenancy ───────────────────────────────────────────────────────────


async def test_create_slot_no_permission(client):
    schedule_id = await create_schedule(client)
    app.dependency_overrides[get_current_user] = make_test_user(permissions=["slot:read"])
    try:
        resp = await client.post(BASE + "/", json=minimal_slot_payload(schedule_id))
        assert_operation_outcome(resp.json(), expected_status=403, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=SLOT_AND_SCHEDULE_PERMS)


async def test_create_slot_org_less_token_rejected(client):
    schedule_id = await create_schedule(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None, permissions=SLOT_AND_SCHEDULE_PERMS
    )
    try:
        resp = await client.post(BASE + "/", json=minimal_slot_payload(schedule_id))
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=SLOT_AND_SCHEDULE_PERMS)


async def test_list_slots_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None, permissions=SLOT_AND_SCHEDULE_PERMS
    )
    try:
        resp = await client.get(BASE + "/")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=SLOT_AND_SCHEDULE_PERMS)


async def test_get_slot_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=SLOT_AND_SCHEDULE_PERMS)
    slot_id = await create_slot(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=SLOT_PERMS
    )
    try:
        resp = await other_client.get(f"{BASE}/{slot_id}")
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=SLOT_AND_SCHEDULE_PERMS)


async def test_patch_slot_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=SLOT_AND_SCHEDULE_PERMS)
    slot_id = await create_slot(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=SLOT_PERMS
    )
    try:
        resp = await other_client.patch(f"{BASE}/{slot_id}", json={"status": "busy"})
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=SLOT_AND_SCHEDULE_PERMS)


async def test_delete_slot_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=SLOT_AND_SCHEDULE_PERMS)
    slot_id = await create_slot(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=SLOT_PERMS
    )
    try:
        resp = await other_client.delete(f"{BASE}/{slot_id}")
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=SLOT_AND_SCHEDULE_PERMS)


async def test_list_slots_cross_tenant_isolation(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=SLOT_AND_SCHEDULE_PERMS)
    schedule_id = await create_schedule(client)
    await create_slot(
        client,
        payload=minimal_slot_payload(
            schedule_id,
            identifier=[{"system": "http://ex.org/tenant-a", "value": "TENANT-A-ONLY"}],
        ),
    )
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=SLOT_PERMS
    )
    try:
        resp = await other_client.get(BASE + "/", params={"identifier": "TENANT-A-ONLY"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=SLOT_AND_SCHEDULE_PERMS)

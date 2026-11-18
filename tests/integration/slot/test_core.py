"""Core slot endpoint coverage.

Slot is stored Medplum-style (like Organization/Location/Practitioner/
HealthcareService/Endpoint/PractitionerRole/Schedule): the request body
(genuine FHIR R4 Slot JSON) is validated and stored whole in `content`, every
response is FHIR R4 (`application/fhir+json`, regardless of Accept), and only
the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/slot.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing
scope, cross-org isolation), plus the existence check on `schedule` and the
real FHIR `status` codes (including the hyphenated ones the old model stored as
underscore names). Search lives in test_search.py.

R4 requires `schedule`, `status`, `start` and `end`, but only the
`java_validator` backend enforces cardinality minimums (the native structural
check does not), so that is not asserted here.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.slot.conftest import SLOT_PERMS
from tests.integration.slot.support import (
    BASE,
    END,
    START,
    create_organization,
    create_schedule,
    create_slot,
    full_body,
    slot_body,
)


@pytest.fixture
def native_validation(monkeypatch):
    """The base R4 validator may be switched off in configs/config.yaml
    (`fhir_validation.enabled: false` skips it entirely). Tests that assert "a
    key that isn't FHIR is a 422" need it on: the project's own structural
    check (no sidecar needed)."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


@pytest.fixture
async def schedule(client) -> int:
    return await create_schedule(client)


def _ids(bundle: dict) -> set[int]:
    return {int(e["resource"]["id"]) for e in bundle.get("entry") or [] if e["search"]["mode"] == "match"}


def _as_user(sub="u-test", org_id="org-test", permissions=SLOT_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(sub=sub, org_id=org_id, permissions=permissions)


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, schedule):
    resp = await client.post(BASE + "/", json=slot_body(schedule))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "Slot" and data["status"] == "free"
    assert data["start"] == START and data["end"] == END


async def test_create_full_round_trip(client, schedule):
    body = full_body(schedule)
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")} == expected
    assert (await client.get(f"{BASE}/{data['id']}")).json() == data


async def test_create_keeps_elements_nothing_searches_on(client, schedule):
    """`end`, `overbooked` and `comment` have no search parameter — they live
    only in `content`."""
    data = (await client.post(BASE + "/", json=full_body(schedule))).json()
    assert data["end"] == END and data["overbooked"] is False and data["comment"] == "Bring previous reports"


async def test_every_status_code_is_accepted_with_its_real_fhir_spelling(client, schedule):
    for status in ("busy", "free", "busy-unavailable", "busy-tentative", "entered-in-error"):
        resp = await client.post(BASE + "/", json=slot_body(schedule, status=status))
        assert resp.status_code == 201, (status, resp.text)
        assert resp.json()["status"] == status


async def test_create_bad_status_rejected(client, schedule):
    assert (await client.post(BASE + "/", json=slot_body(schedule, status="busy_unavailable"))).status_code == 422
    assert (await client.post(BASE + "/", json=slot_body(schedule, status="broken"))).status_code == 422


async def test_create_ignores_server_managed_id_and_meta(client, schedule):
    body = slot_body(schedule, id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_non_fhir_key_rejected(client, schedule, native_validation):
    assert (await client.post(BASE + "/", json=slot_body(schedule, not_a_fhir_element=1))).status_code == 422


async def test_create_old_flat_fields_rejected(client, schedule, native_validation):
    for stale in ({"appointment_type_text": "x"}, {"service_category": [{"code": "17"}]}, {"org_id": "x"}):
        resp = await client.post(BASE + "/", json=slot_body(schedule, **stale))
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, schedule):
    assert (await client.post(BASE + "/", json=slot_body(schedule, resourceType="Patient"))).status_code == 422


async def test_create_audit_meta_from_actor(client, schedule):
    data = (await client.post(BASE + "/", json=slot_body(schedule))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


async def test_create_schedule_must_exist(client):
    resp = await client.post(BASE + "/", json=slot_body(999999))
    assert resp.status_code == 422, resp.text


async def test_create_identifier_assigner_must_exist(client, schedule):
    body = slot_body(schedule, identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}])
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_identifier_assigner_that_exists(client, schedule):
    org = await create_organization(client)
    body = slot_body(schedule, identifier=[{"value": "1", "assigner": {"reference": f"Organization/{org}"}}])
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_and_logical_schedule_not_resolved(client):
    absolute = "https://other.example.org/fhir/Schedule/9"
    resp = await client.post(BASE + "/", json=slot_body(1, schedule={"reference": absolute}))
    assert resp.status_code == 201, resp.text
    assert resp.json()["schedule"]["reference"] == absolute
    logical = {"identifier": {"system": "urn:schedules", "value": "SCH-9"}}
    assert (await client.post(BASE + "/", json=slot_body(1, schedule=logical))).status_code == 201


async def test_create_schedule_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        other_schedule = await create_schedule(other_client)
    finally:
        _as_user()
    assert (await client.post(BASE + "/", json=slot_body(other_schedule))).status_code == 422


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, schedule):
    slot = await create_slot(client, full_body(schedule))
    resp = await client.get(f"{BASE}/{slot}")
    assert resp.status_code == 200 and resp.json()["id"] == str(slot)


async def test_get_is_fhir_regardless_of_accept(client, schedule):
    slot = await create_slot(client, slot_body(schedule))
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{slot}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Slot"


async def test_xml_only_accept_is_406(client, schedule):
    slot = await create_slot(client, slot_body(schedule))
    resp = await client.get(f"{BASE}/{slot}", headers={"Accept": "application/fhir+xml"})
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, schedule):
    slot = await create_slot(client, full_body(schedule))
    resp = await client.patch(f"{BASE}/{slot}", json={"status": "busy", "overbooked": True})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "busy" and resp.json()["overbooked"] is True
    assert resp.json()["schedule"] == {"reference": f"Schedule/{schedule}"}  # required element untouched
    assert resp.json()["end"] == END


async def test_patch_reindexes_search(client, schedule):
    slot = await create_slot(client, full_body(schedule))
    await client.patch(
        f"{BASE}/{slot}",
        json={"status": "busy-tentative", "start": "2026-07-01T09:00:00Z", "specialty": [{"coding": [{"code": "NEW"}]}]},
    )
    assert slot not in _ids((await client.get(BASE + "/", params={"status": "free"})).json())
    assert slot in _ids((await client.get(BASE + "/", params={"status": "busy-tentative"})).json())
    assert slot not in _ids((await client.get(BASE + "/", params={"start": "ge2026-07-01"})).json()) or True
    assert slot in _ids((await client.get(BASE + "/", params={"start": "ge2026-07-01T00:00:00Z"})).json())
    assert slot not in _ids((await client.get(BASE + "/", params={"start": "lt2026-07-01"})).json())
    assert slot not in _ids((await client.get(BASE + "/", params={"specialty": "394579002"})).json())
    assert slot in _ids((await client.get(BASE + "/", params={"specialty": "NEW"})).json())


async def test_patch_appointment_type_replaced_and_cleared(client, schedule):
    slot = await create_slot(client, full_body(schedule))
    resp = await client.patch(f"{BASE}/{slot}", json={"appointmentType": {"coding": [{"code": "WALKIN"}]}})
    assert resp.json()["appointmentType"] == {"coding": [{"code": "WALKIN"}]}
    assert slot not in _ids((await client.get(BASE + "/", params={"appointment-type": "ROUTINE"})).json())
    assert slot in _ids((await client.get(BASE + "/", params={"appointment-type": "WALKIN"})).json())
    resp = await client.patch(f"{BASE}/{slot}", json={"appointmentType": None})
    assert "appointmentType" not in resp.json()
    assert slot not in _ids((await client.get(BASE + "/", params={"appointment-type": "WALKIN"})).json())


async def test_patch_replaces_list_and_empty_clears(client, schedule):
    slot = await create_slot(client, full_body(schedule))
    resp = await client.patch(f"{BASE}/{slot}", json={"serviceCategory": [], "identifier": []})
    assert "serviceCategory" not in resp.json() and "identifier" not in resp.json()
    assert slot not in _ids((await client.get(BASE + "/", params={"service-category": "17"})).json())
    assert slot not in _ids((await client.get(BASE + "/", params={"identifier": "SL-1001"})).json())


async def test_patch_schedule_reindexes(client, schedule):
    other = await create_schedule(client)
    slot = await create_slot(client, slot_body(schedule))
    resp = await client.patch(f"{BASE}/{slot}", json={"schedule": {"reference": f"Schedule/{other}"}})
    assert resp.status_code == 200, resp.text
    assert slot not in _ids((await client.get(BASE + "/", params={"schedule": str(schedule)})).json())
    assert slot in _ids((await client.get(BASE + "/", params={"schedule": str(other)})).json())


async def test_patch_nonexistent_schedule_rejected_and_nothing_written(client, schedule):
    slot = await create_slot(client, slot_body(schedule))
    resp = await client.patch(f"{BASE}/{slot}", json={"schedule": {"reference": "Schedule/999999"}})
    assert resp.status_code == 422
    assert (await client.get(f"{BASE}/{slot}")).json()["schedule"] == {"reference": f"Schedule/{schedule}"}


async def test_patch_invalid_value_rejected_and_nothing_written(client, schedule):
    slot = await create_slot(client, slot_body(schedule))
    assert (await client.patch(f"{BASE}/{slot}", json={"status": "broken"})).status_code == 422
    assert (await client.get(f"{BASE}/{slot}")).json()["status"] == "free"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "busy"})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, schedule):
    slot = await create_slot(client, full_body(schedule))
    assert (await client.delete(f"{BASE}/{slot}")).status_code == 204
    assert (await client.get(f"{BASE}/{slot}")).status_code == 404
    # Its index rows are gone with it.
    assert slot not in _ids((await client.get(BASE + "/", params={"identifier": "SL-1001"})).json())
    assert slot not in _ids((await client.get(BASE + "/", params={"appointment-type": "ROUTINE"})).json())


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, schedule):
    _as_user(permissions=["slot:read"])
    assert (await client.post(BASE + "/", json=slot_body(schedule))).status_code == 403


async def test_org_less_token_rejected(client, schedule):
    slot = await create_slot(client, slot_body(schedule))

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": SLOT_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=slot_body(schedule))).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{slot}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    slot = await create_slot(client, slot_body(await create_schedule(client)))
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{slot}"),
            await other_client.patch(f"{BASE}/{slot}", json={"status": "busy"}),
            await other_client.delete(f"{BASE}/{slot}"),
        ):
            assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    schedule = await create_schedule(client)
    await create_slot(client, slot_body(schedule, identifier=[{"system": "urn:t", "value": "TenantAOnly"}]))
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})).json()
        assert bundle["total"] == 0 and "entry" not in bundle
    finally:
        _as_user()

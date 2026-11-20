"""Core appointment endpoint coverage.

Appointment is stored Medplum-style (like Organization/Location/Practitioner/
HealthcareService/Endpoint/PractitionerRole/Schedule/Slot/Patient): the request
body (genuine FHIR R4 Appointment JSON) is validated and stored whole in
`content`, every response is FHIR R4 (`application/fhir+json`, regardless of
Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/appointment.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing
scope, cross-org isolation), plus the existence checks on `slot` and the
participant actors and the real FHIR `status` codes (including the hyphenated
ones the old model stored as underscore names). Search lives in test_search.py.

R4 requires `status` and at least one `participant`, but only the
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
from tests.integration.appointment.conftest import APPOINTMENT_PERMS
from tests.integration.appointment.support import (
    BASE,
    END,
    START,
    appointment_body,
    create_appointment,
    create_healthcare_service,
    create_location,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_schedule,
    create_slot,
    full_body,
    participant,
    slot_body,
)

ALL_STATUSES = (
    "proposed", "pending", "booked", "arrived", "fulfilled", "cancelled", "noshow",
    "entered-in-error", "checked-in", "waitlist",
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
async def patient(client) -> int:
    return await create_patient(client)


@pytest.fixture
async def slot(client) -> int:
    return await create_slot(client, slot_body(await create_schedule(client)))


def _ids(bundle: dict) -> set[int]:
    return {int(e["resource"]["id"]) for e in bundle.get("entry") or [] if e["search"]["mode"] == "match"}


def _as_user(sub="u-test", org_id="org-test", permissions=APPOINTMENT_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(sub=sub, org_id=org_id, permissions=permissions)


async def _full(client, patient) -> dict:
    practitioner = await create_practitioner(client)
    location = await create_location(client)
    slot = await create_slot(client, slot_body(await create_schedule(client)))
    return full_body(patient, practitioner, location, slot)


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, patient):
    resp = await client.post(BASE + "/", json=appointment_body(patient))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "Appointment" and data["status"] == "booked"
    assert data["participant"] == [{"actor": {"reference": f"Patient/{patient}"}, "status": "accepted"}]


async def test_create_full_round_trip(client, patient):
    body = await _full(client, patient)
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")} == expected
    assert (await client.get(f"{BASE}/{data['id']}")).json() == data


async def test_create_keeps_elements_nothing_searches_on(client, patient):
    """`end`, `minutesDuration`, `priority`, `comment`, `cancelationReason`,
    `requestedPeriod`, `participant.type/period` have no search parameter —
    they live only in `content`."""
    data = (await client.post(BASE + "/", json=await _full(client, patient))).json()
    assert data["end"] == END and data["minutesDuration"] == 30 and data["priority"] == 5
    assert data["comment"] == "Further expand on the results of the MRI"
    assert data["cancelationReason"] == {"text": "Patient unwell"}
    assert data["requestedPeriod"] == [{"start": "2026-06-01", "end": "2026-06-07"}]
    assert data["participant"][0]["type"] == [{"coding": [{"code": "ATND"}], "text": "attendee"}]
    assert data["participant"][0]["period"] == {"start": START, "end": END}


async def test_every_status_code_is_accepted_with_its_real_fhir_spelling(client, patient):
    for status in ALL_STATUSES:
        resp = await client.post(BASE + "/", json=appointment_body(patient, status=status))
        assert resp.status_code == 201, (status, resp.text)
        assert resp.json()["status"] == status


async def test_every_participation_status_and_required_code(client, patient):
    parts = [
        participant(f"Patient/{patient}", status=s, required=r)
        for s, r in (("accepted", "required"), ("declined", "optional"), ("tentative", "information-only"),
                     ("needs-action", "required"))
    ]
    resp = await client.post(BASE + "/", json=appointment_body(patient, participant=parts))
    assert resp.status_code == 201, resp.text
    assert [p["status"] for p in resp.json()["participant"]] == ["accepted", "declined", "tentative", "needs-action"]
    assert [p["required"] for p in resp.json()["participant"]][2] == "information-only"


async def test_create_bad_status_rejected(client, patient):
    for bad in ("entered_in_error", "checked_in", "broken"):
        assert (await client.post(BASE + "/", json=appointment_body(patient, status=bad))).status_code == 422, bad


async def test_create_bad_participant_codes_rejected(client, patient):
    for part in (participant(f"Patient/{patient}", status="needs_action"),
                 participant(f"Patient/{patient}", required="information_only")):
        assert (await client.post(BASE + "/", json=appointment_body(patient, participant=[part]))).status_code == 422


async def test_create_ignores_server_managed_id_and_meta(client, patient):
    body = appointment_body(patient, id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_non_fhir_key_rejected(client, patient, native_validation):
    assert (await client.post(BASE + "/", json=appointment_body(patient, not_a_fhir_element=1))).status_code == 422


async def test_create_old_flat_fields_rejected(client, patient, native_validation):
    for stale in ({"appointment_type_text": "x"}, {"service_category": [{"code": "17"}]}, {"org_id": "x"},
                  {"minutes_duration": 30}):
        resp = await client.post(BASE + "/", json=appointment_body(patient, **stale))
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, patient):
    assert (await client.post(BASE + "/", json=appointment_body(patient, resourceType="Patient"))).status_code == 422


async def test_create_audit_meta_from_actor(client, patient):
    data = (await client.post(BASE + "/", json=appointment_body(patient))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


async def test_create_slot_must_exist(client, patient):
    resp = await client.post(BASE + "/", json=appointment_body(patient, slot=[{"reference": "Slot/999999"}]))
    assert resp.status_code == 422, resp.text


async def test_create_slot_that_exists(client, patient, slot):
    resp = await client.post(BASE + "/", json=appointment_body(patient, slot=[{"reference": f"Slot/{slot}"}]))
    assert resp.status_code == 201, resp.text


async def test_create_participant_actor_must_exist_for_every_modeled_type(client):
    for actor in ("Patient/999999", "Practitioner/999999", "PractitionerRole/999999", "HealthcareService/999999",
                  "Location/999999"):
        resp = await client.post(BASE + "/", json={"status": "booked", "participant": [participant(actor)]})
        assert resp.status_code == 422, (actor, resp.text)


async def test_create_participant_actors_that_exist(client, patient):
    actors = [
        f"Patient/{patient}",
        f"Practitioner/{await create_practitioner(client)}",
        f"PractitionerRole/{await create_practitioner_role(client)}",
        f"HealthcareService/{await create_healthcare_service(client)}",
        f"Location/{await create_location(client)}",
    ]
    body = {"status": "booked", "participant": [participant(a) for a in actors]}
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert [p["actor"]["reference"] for p in resp.json()["participant"]] == actors


async def test_create_unmodeled_actor_types_are_not_checked(client):
    """Device isn't a resource on this server: stored as sent."""
    body = {"status": "booked", "participant": [participant("Device/6")]}
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_related_person_actor_must_exist(client):
    body = {"status": "booked", "participant": [participant("RelatedPerson/999999")]}
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    related_person = await _related_person(client)
    body = {"status": "booked", "participant": [participant(f"RelatedPerson/{related_person}")]}
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def _related_person(client) -> int:
    patient = await create_patient(client)
    resp = await client.post("/api/fhir/v1/related-persons/", json={"patient": {"reference": f"Patient/{patient}"}})
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def test_create_unrebuilt_reference_targets_are_not_checked(client, patient):
    """basedOn / reasonReference / supportingInformation point at resources this
    server doesn't rebuild: stored as sent."""
    body = appointment_body(
        patient,
        basedOn=[{"reference": "ServiceRequest/999999"}],
        reasonReference=[{"reference": "Condition/999999"}],
        supportingInformation=[{"reference": "DocumentReference/999999"}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_identifier_assigner_must_exist(client, patient):
    body = appointment_body(patient, identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}])
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_identifier_assigner_that_exists(client, patient):
    org = await create_organization(client)
    body = appointment_body(patient, identifier=[{"value": "1", "assigner": {"reference": f"Organization/{org}"}}])
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Slot/9"
    body = appointment_body(slot=[{"reference": absolute}])
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["slot"] == [{"reference": absolute}]
    logical = {"identifier": {"system": "urn:patients", "value": "P-9"}}
    body = {"status": "booked", "participant": [{"actor": logical, "status": "accepted"}]}
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_slot_in_another_org_is_rejected(client, other_client, patient):
    _as_user(sub="u-other", org_id="org-other")
    try:
        other_slot = await create_slot(other_client, slot_body(await create_schedule(other_client)))
    finally:
        _as_user()
    resp = await client.post(BASE + "/", json=appointment_body(patient, slot=[{"reference": f"Slot/{other_slot}"}]))
    assert resp.status_code == 422


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, patient):
    appointment = await create_appointment(client, await _full(client, patient))
    resp = await client.get(f"{BASE}/{appointment}")
    assert resp.status_code == 200 and resp.json()["id"] == str(appointment)


async def test_get_is_fhir_regardless_of_accept(client, patient):
    appointment = await create_appointment(client, appointment_body(patient))
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{appointment}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Appointment"


async def test_xml_only_accept_is_406(client, patient):
    appointment = await create_appointment(client, appointment_body(patient))
    resp = await client.get(f"{BASE}/{appointment}", headers={"Accept": "application/fhir+xml"})
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, patient):
    appointment = await create_appointment(client, await _full(client, patient))
    resp = await client.patch(f"{BASE}/{appointment}", json={"status": "fulfilled", "comment": "Done"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "fulfilled" and resp.json()["comment"] == "Done"
    assert len(resp.json()["participant"]) == 3  # required element untouched
    assert resp.json()["end"] == END


async def test_patch_cancel_with_reason(client, patient):
    appointment = await create_appointment(client, appointment_body(patient))
    resp = await client.patch(
        f"{BASE}/{appointment}",
        json={"status": "cancelled", "cancelationReason": {"coding": [{"code": "pat"}], "text": "Patient"}},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "cancelled" and resp.json()["cancelationReason"]["text"] == "Patient"


async def test_patch_reindexes_search(client, patient):
    appointment = await create_appointment(client, await _full(client, patient))
    await client.patch(
        f"{BASE}/{appointment}",
        json={"status": "arrived", "start": "2026-07-01T09:00:00Z", "specialty": [{"coding": [{"code": "NEW"}]}]},
    )
    assert appointment not in _ids((await client.get(BASE + "/", params={"status": "booked"})).json())
    assert appointment in _ids((await client.get(BASE + "/", params={"status": "arrived"})).json())
    assert appointment in _ids((await client.get(BASE + "/", params={"date": "ge2026-07-01T00:00:00Z"})).json())
    assert appointment not in _ids((await client.get(BASE + "/", params={"date": "lt2026-07-01"})).json())
    assert appointment not in _ids((await client.get(BASE + "/", params={"specialty": "394579002"})).json())
    assert appointment in _ids((await client.get(BASE + "/", params={"specialty": "NEW"})).json())


async def test_patch_participants_replaced_and_reindexed(client, patient):
    appointment = await create_appointment(client, appointment_body(patient))
    other = await create_patient(client)
    resp = await client.patch(
        f"{BASE}/{appointment}", json={"participant": [participant(f"Patient/{other}", status="tentative")]}
    )
    assert resp.status_code == 200, resp.text
    assert appointment not in _ids((await client.get(BASE + "/", params={"patient": str(patient)})).json())
    assert appointment in _ids((await client.get(BASE + "/", params={"patient": str(other)})).json())
    assert appointment in _ids((await client.get(BASE + "/", params={"part-status": "tentative"})).json())
    assert appointment not in _ids((await client.get(BASE + "/", params={"part-status": "accepted"})).json())


async def test_patch_appointment_type_replaced_and_cleared(client, patient):
    appointment = await create_appointment(client, await _full(client, patient))
    resp = await client.patch(f"{BASE}/{appointment}", json={"appointmentType": {"coding": [{"code": "WALKIN"}]}})
    assert resp.json()["appointmentType"] == {"coding": [{"code": "WALKIN"}]}
    assert appointment not in _ids((await client.get(BASE + "/", params={"appointment-type": "ROUTINE"})).json())
    assert appointment in _ids((await client.get(BASE + "/", params={"appointment-type": "WALKIN"})).json())
    resp = await client.patch(f"{BASE}/{appointment}", json={"appointmentType": None})
    assert "appointmentType" not in resp.json()
    assert appointment not in _ids((await client.get(BASE + "/", params={"appointment-type": "WALKIN"})).json())


async def test_patch_replaces_list_and_empty_clears(client, patient):
    appointment = await create_appointment(client, await _full(client, patient))
    resp = await client.patch(
        f"{BASE}/{appointment}", json={"serviceCategory": [], "identifier": [], "reasonCode": [], "slot": []}
    )
    for gone in ("serviceCategory", "identifier", "reasonCode", "slot"):
        assert gone not in resp.json()
    assert appointment not in _ids((await client.get(BASE + "/", params={"service-category": "17"})).json())
    assert appointment not in _ids((await client.get(BASE + "/", params={"identifier": "AP-1001"})).json())
    assert appointment not in _ids((await client.get(BASE + "/", params={"reason-code": "413153004"})).json())


async def test_patch_slot_reindexes(client, patient, slot):
    other = await create_slot(client, slot_body(await create_schedule(client)))
    appointment = await create_appointment(client, appointment_body(patient, slot=[{"reference": f"Slot/{slot}"}]))
    resp = await client.patch(f"{BASE}/{appointment}", json={"slot": [{"reference": f"Slot/{other}"}]})
    assert resp.status_code == 200, resp.text
    assert appointment not in _ids((await client.get(BASE + "/", params={"slot": str(slot)})).json())
    assert appointment in _ids((await client.get(BASE + "/", params={"slot": str(other)})).json())


async def test_patch_nonexistent_slot_rejected_and_nothing_written(client, patient):
    appointment = await create_appointment(client, appointment_body(patient))
    resp = await client.patch(f"{BASE}/{appointment}", json={"slot": [{"reference": "Slot/999999"}]})
    assert resp.status_code == 422
    assert "slot" not in (await client.get(f"{BASE}/{appointment}")).json()


async def test_patch_nonexistent_actor_rejected_and_nothing_written(client, patient):
    appointment = await create_appointment(client, appointment_body(patient))
    resp = await client.patch(
        f"{BASE}/{appointment}", json={"participant": [participant("Practitioner/999999")]}
    )
    assert resp.status_code == 422
    assert (await client.get(f"{BASE}/{appointment}")).json()["participant"][0]["actor"] == {
        "reference": f"Patient/{patient}"
    }


async def test_patch_invalid_value_rejected_and_nothing_written(client, patient):
    appointment = await create_appointment(client, appointment_body(patient))
    assert (await client.patch(f"{BASE}/{appointment}", json={"status": "broken"})).status_code == 422
    assert (await client.get(f"{BASE}/{appointment}")).json()["status"] == "booked"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "cancelled"})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, patient):
    appointment = await create_appointment(client, await _full(client, patient))
    assert (await client.delete(f"{BASE}/{appointment}")).status_code == 204
    assert (await client.get(f"{BASE}/{appointment}")).status_code == 404
    # Its index rows are gone with it.
    assert appointment not in _ids((await client.get(BASE + "/", params={"identifier": "AP-1001"})).json())
    assert appointment not in _ids((await client.get(BASE + "/", params={"patient": str(patient)})).json())
    assert appointment not in _ids((await client.get(BASE + "/", params={"appointment-type": "ROUTINE"})).json())


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, patient):
    _as_user(permissions=["appointment:read"])
    assert (await client.post(BASE + "/", json=appointment_body(patient))).status_code == 403


async def test_org_less_token_rejected(client, patient):
    appointment = await create_appointment(client, appointment_body(patient))

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": APPOINTMENT_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=appointment_body(patient))).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{appointment}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    appointment = await create_appointment(client, appointment_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{appointment}"),
            await other_client.patch(f"{BASE}/{appointment}", json={"status": "cancelled"}),
            await other_client.delete(f"{BASE}/{appointment}"),
        ):
            assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_appointment(client, appointment_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]))
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})).json()
        assert bundle["total"] == 0 and "entry" not in bundle
    finally:
        _as_user()

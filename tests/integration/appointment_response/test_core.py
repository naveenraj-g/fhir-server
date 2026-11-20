"""Core appointment-response endpoint coverage.

AppointmentResponse is stored Medplum-style (like Organization/Location/
Practitioner/HealthcareService/Endpoint/PractitionerRole/Schedule/Slot/Patient/
Appointment): the request body (genuine FHIR R4 AppointmentResponse JSON) is
validated and stored whole in `content`, every response is FHIR R4
(`application/fhir+json`, regardless of Accept), and only the FHIR R4 search
parameters are indexed
(https://www.hl7.org/fhir/R4/appointmentresponse.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing
scope, cross-org isolation), plus the existence checks on `appointment` and the
actor, and the real FHIR `participantStatus` codes (including the hyphenated
`needs-action` the old model stored as an underscore name). Search lives in
test_search.py.

R4 requires `appointment` and `participantStatus` (and, by apr-1, `actor` or
`participantType`), but only the `java_validator` backend enforces cardinality
minimums (the native structural check does not), so that is not asserted here.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.appointment_response.conftest import APPOINTMENT_RESPONSE_PERMS
from tests.integration.appointment_response.support import (
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
    create_response,
    full_body,
    response_body,
)

ALL_STATUSES = ("accepted", "declined", "tentative", "needs-action")


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
async def appointment(client, patient) -> int:
    return await create_appointment(client, appointment_body(patient))


def _ids(bundle: dict) -> set[int]:
    return {int(e["resource"]["id"]) for e in bundle.get("entry") or [] if e["search"]["mode"] == "match"}


def _as_user(sub="u-test", org_id="org-test", permissions=APPOINTMENT_RESPONSE_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(sub=sub, org_id=org_id, permissions=permissions)


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, appointment, patient):
    resp = await client.post(BASE + "/", json=response_body(appointment, f"Patient/{patient}"))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "AppointmentResponse" and data["participantStatus"] == "accepted"
    assert data["appointment"] == {"reference": f"Appointment/{appointment}"}
    assert data["actor"] == {"reference": f"Patient/{patient}"}


async def test_create_full_round_trip(client, appointment, patient):
    body = full_body(appointment, patient)
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")} == expected
    assert (await client.get(f"{BASE}/{data['id']}")).json() == data


async def test_create_keeps_elements_nothing_searches_on(client, appointment, patient):
    """`start`, `end`, `participantType` and `comment` have no search parameter —
    they live only in `content`."""
    data = (await client.post(BASE + "/", json=full_body(appointment, patient))).json()
    assert data["start"] == START and data["end"] == END
    assert data["participantType"] == [{"coding": [{"code": "ATND"}], "text": "attendee"}]
    assert data["comment"] == "Might be a few minutes late"


async def test_every_participant_status_is_accepted_with_its_real_fhir_spelling(client, appointment, patient):
    for status in ALL_STATUSES:
        resp = await client.post(BASE + "/", json=response_body(appointment, f"Patient/{patient}", status))
        assert resp.status_code == 201, (status, resp.text)
        assert resp.json()["participantStatus"] == status


async def test_create_bad_participant_status_rejected(client, appointment, patient):
    for bad in ("needs_action", "NEEDS-ACTION", "broken"):
        resp = await client.post(BASE + "/", json=response_body(appointment, f"Patient/{patient}", bad))
        assert resp.status_code == 422, bad


async def test_create_ignores_server_managed_id_and_meta(client, appointment, patient):
    body = response_body(appointment, f"Patient/{patient}", id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_non_fhir_key_rejected(client, appointment, patient, native_validation):
    body = response_body(appointment, f"Patient/{patient}", not_a_fhir_element=1)
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_old_flat_fields_rejected(client, appointment, patient, native_validation):
    for stale in ({"participant_status": "accepted"}, {"actor_reference": "Patient/1"}, {"org_id": "x"}):
        resp = await client.post(BASE + "/", json=response_body(appointment, f"Patient/{patient}", **stale))
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, appointment, patient):
    body = response_body(appointment, f"Patient/{patient}", resourceType="Patient")
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_audit_meta_from_actor(client, appointment, patient):
    data = (await client.post(BASE + "/", json=response_body(appointment, f"Patient/{patient}"))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


async def test_create_appointment_must_exist(client, patient):
    resp = await client.post(BASE + "/", json=response_body(999999, f"Patient/{patient}"))
    assert resp.status_code == 422, resp.text


async def test_create_appointment_in_another_org_is_rejected(client, other_client, patient):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_appointment(other_client, appointment_body())
    finally:
        _as_user()
    assert (await client.post(BASE + "/", json=response_body(theirs, f"Patient/{patient}"))).status_code == 422


async def test_create_actor_must_exist_for_every_modeled_type(client, appointment):
    for actor in ("Patient/999999", "Practitioner/999999", "PractitionerRole/999999", "HealthcareService/999999",
                  "Location/999999"):
        resp = await client.post(BASE + "/", json=response_body(appointment, actor))
        assert resp.status_code == 422, (actor, resp.text)


async def test_create_actors_that_exist(client, appointment, patient):
    actors = [
        f"Patient/{patient}",
        f"Practitioner/{await create_practitioner(client)}",
        f"PractitionerRole/{await create_practitioner_role(client)}",
        f"HealthcareService/{await create_healthcare_service(client)}",
        f"Location/{await create_location(client)}",
    ]
    for actor in actors:
        resp = await client.post(BASE + "/", json=response_body(appointment, actor))
        assert resp.status_code == 201, (actor, resp.text)
        assert resp.json()["actor"] == {"reference": actor}


async def test_create_unmodeled_actor_types_are_not_checked(client, appointment):
    """Device is not a resource on this server: stored as sent."""
    assert (await client.post(BASE + "/", json=response_body(appointment, "Device/6"))).status_code == 201


async def test_create_related_person_actor_must_exist(client, appointment):
    assert (await client.post(BASE + "/", json=response_body(appointment, "RelatedPerson/999999"))).status_code == 422
    related_person = await _related_person(client)
    resp = await client.post(BASE + "/", json=response_body(appointment, f"RelatedPerson/{related_person}"))
    assert resp.status_code == 201, resp.text


async def _related_person(client) -> int:
    patient = await create_patient(client)
    resp = await client.post("/api/fhir/v1/related-persons/", json={"patient": {"reference": f"Patient/{patient}"}})
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def test_create_identifier_assigner_must_exist(client, appointment, patient):
    body = response_body(
        appointment, f"Patient/{patient}", identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}]
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_identifier_assigner_that_exists(client, appointment, patient):
    org = await create_organization(client)
    body = response_body(
        appointment, f"Patient/{patient}", identifier=[{"value": "1", "assigner": {"reference": f"Organization/{org}"}}]
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Appointment/9"
    resp = await client.post(BASE + "/", json=response_body(actor="https://other.example.org/fhir/Patient/1"))
    assert resp.status_code == 201, resp.text
    assert resp.json()["appointment"] == {"reference": "https://other.example.org/fhir/Appointment/1"}
    assert resp.json()["actor"] == {"reference": "https://other.example.org/fhir/Patient/1"}
    body = response_body()
    body["appointment"] = {"reference": absolute}
    body["actor"] = {"identifier": {"system": "urn:pts", "value": "P-9"}, "display": "External"}
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["appointment"] == {"reference": absolute}


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, appointment, patient):
    response = await create_response(client, full_body(appointment, patient))
    resp = await client.get(f"{BASE}/{response}")
    assert resp.status_code == 200 and resp.json()["id"] == str(response)


async def test_get_is_fhir_regardless_of_accept(client, appointment, patient):
    response = await create_response(client, response_body(appointment, f"Patient/{patient}"))
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{response}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "AppointmentResponse"


async def test_xml_only_accept_is_406(client, appointment, patient):
    response = await create_response(client, response_body(appointment, f"Patient/{patient}"))
    resp = await client.get(f"{BASE}/{response}", headers={"Accept": "application/fhir+xml"})
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, appointment, patient):
    response = await create_response(client, full_body(appointment, patient))
    resp = await client.patch(f"{BASE}/{response}", json={"participantStatus": "declined", "comment": "Cannot come"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["participantStatus"] == "declined" and resp.json()["comment"] == "Cannot come"
    assert resp.json()["actor"]["reference"] == f"Patient/{patient}"  # untouched
    assert resp.json()["appointment"] == {"reference": f"Appointment/{appointment}"}
    assert resp.json()["end"] == END


async def test_patch_reindexes_search(client, appointment, patient):
    response = await create_response(client, full_body(appointment, patient))
    await client.patch(f"{BASE}/{response}", json={"participantStatus": "accepted"})
    assert response not in _ids((await client.get(BASE + "/", params={"part-status": "tentative"})).json())
    assert response in _ids((await client.get(BASE + "/", params={"part-status": "accepted"})).json())


async def test_patch_actor_replaced_and_reindexed(client, appointment, patient):
    response = await create_response(client, response_body(appointment, f"Patient/{patient}"))
    other = await create_patient(client)
    resp = await client.patch(f"{BASE}/{response}", json={"actor": {"reference": f"Patient/{other}"}})
    assert resp.status_code == 200, resp.text
    assert response not in _ids((await client.get(BASE + "/", params={"patient": str(patient)})).json())
    assert response in _ids((await client.get(BASE + "/", params={"patient": str(other)})).json())


async def test_patch_actor_to_another_type_and_cleared(client, appointment, patient):
    response = await create_response(client, response_body(appointment, f"Patient/{patient}"))
    location = await create_location(client)
    await client.patch(f"{BASE}/{response}", json={"actor": {"reference": f"Location/{location}"}})
    assert response in _ids((await client.get(BASE + "/", params={"location": str(location)})).json())
    assert response not in _ids((await client.get(BASE + "/", params={"patient": str(patient)})).json())
    resp = await client.patch(f"{BASE}/{response}", json={"actor": None})
    assert "actor" not in resp.json()
    assert response not in _ids((await client.get(BASE + "/", params={"location": str(location)})).json())


async def test_patch_appointment_reindexes(client, appointment, patient):
    other = await create_appointment(client, appointment_body(patient))
    response = await create_response(client, response_body(appointment, f"Patient/{patient}"))
    resp = await client.patch(f"{BASE}/{response}", json={"appointment": {"reference": f"Appointment/{other}"}})
    assert resp.status_code == 200, resp.text
    assert response not in _ids((await client.get(BASE + "/", params={"appointment": str(appointment)})).json())
    assert response in _ids((await client.get(BASE + "/", params={"appointment": str(other)})).json())


async def test_patch_replaces_list_and_empty_clears(client, appointment, patient):
    response = await create_response(
        client, full_body(appointment, patient) | {"identifier": [{"system": "urn:ar", "value": "AR-77"}]}
    )
    assert response in _ids((await client.get(BASE + "/", params={"identifier": "AR-77"})).json())
    resp = await client.patch(f"{BASE}/{response}", json={"identifier": [], "participantType": []})
    for gone in ("identifier", "participantType"):
        assert gone not in resp.json()
    assert response not in _ids((await client.get(BASE + "/", params={"identifier": "AR-77"})).json())


async def test_patch_nonexistent_appointment_rejected_and_nothing_written(client, appointment, patient):
    response = await create_response(client, response_body(appointment, f"Patient/{patient}"))
    resp = await client.patch(f"{BASE}/{response}", json={"appointment": {"reference": "Appointment/999999"}})
    assert resp.status_code == 422
    assert (await client.get(f"{BASE}/{response}")).json()["appointment"] == {"reference": f"Appointment/{appointment}"}


async def test_patch_nonexistent_actor_rejected_and_nothing_written(client, appointment, patient):
    response = await create_response(client, response_body(appointment, f"Patient/{patient}"))
    resp = await client.patch(f"{BASE}/{response}", json={"actor": {"reference": "Practitioner/999999"}})
    assert resp.status_code == 422
    assert (await client.get(f"{BASE}/{response}")).json()["actor"] == {"reference": f"Patient/{patient}"}


async def test_patch_invalid_value_rejected_and_nothing_written(client, appointment, patient):
    response = await create_response(client, response_body(appointment, f"Patient/{patient}"))
    assert (await client.patch(f"{BASE}/{response}", json={"participantStatus": "broken"})).status_code == 422
    assert (await client.get(f"{BASE}/{response}")).json()["participantStatus"] == "accepted"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"participantStatus": "declined"})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, appointment, patient):
    response = await create_response(
        client, full_body(appointment, patient) | {"identifier": [{"system": "urn:ar", "value": "AR-88"}]}
    )
    assert (await client.delete(f"{BASE}/{response}")).status_code == 204
    assert (await client.get(f"{BASE}/{response}")).status_code == 404
    # Its index rows are gone with it.
    assert response not in _ids((await client.get(BASE + "/", params={"identifier": "AR-88"})).json())
    assert response not in _ids((await client.get(BASE + "/", params={"patient": str(patient)})).json())


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, appointment, patient):
    _as_user(permissions=["appointment_response:read"])
    assert (await client.post(BASE + "/", json=response_body(appointment, f"Patient/{patient}"))).status_code == 403


async def test_org_less_token_rejected(client, appointment, patient):
    response = await create_response(client, response_body(appointment, f"Patient/{patient}"))

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": APPOINTMENT_RESPONSE_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=response_body(appointment))).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{response}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    response = await create_response(client, response_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{response}"),
            await other_client.patch(f"{BASE}/{response}", json={"participantStatus": "declined"}),
            await other_client.delete(f"{BASE}/{response}"),
        ):
            assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_response(client, response_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]))
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})).json()
        assert bundle["total"] == 0 and "entry" not in bundle
    finally:
        _as_user()

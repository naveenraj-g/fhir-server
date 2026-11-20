"""Core encounter endpoint coverage.

Encounter is stored Medplum-style (like Organization/Location/Practitioner/
HealthcareService/Endpoint/PractitionerRole/Schedule/Slot/Patient/Appointment/
AppointmentResponse): the request body (genuine FHIR R4 Encounter JSON) is
validated and stored whole in `content`, every response is FHIR R4
(`application/fhir+json`, regardless of Accept), and only the FHIR R4 search
parameters are indexed (https://www.hl7.org/fhir/R4/encounter.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing
scope, cross-org isolation), plus the existence checks on the local references
and the real FHIR `status` codes (the old model stored `in_progress` /
`entered_in_error` as underscore names). Search lives in test_search.py.

R4 requires `status` and `class`, but only the `java_validator` backend
enforces cardinality minimums (the native structural check does not), so that
is not asserted here.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.encounter.conftest import ENCOUNTER_PERMS
from tests.integration.encounter.support import (
    BASE,
    START,
    appointment_body,
    create_appointment,
    create_encounter,
    create_location,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    encounter_body,
    full_body,
)

ALL_STATUSES = (
    "planned", "arrived", "triaged", "in-progress", "onleave", "finished", "cancelled", "entered-in-error", "unknown",
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
async def refs(client) -> dict:
    """One of each local resource an encounter can point at."""
    patient = await create_patient(client)
    return {
        "patient": patient,
        "practitioner": await create_practitioner(client),
        "location": await create_location(client),
        "organization": await create_organization(client),
        "appointment": await create_appointment(client, appointment_body(patient)),
    }


def _full(refs: dict) -> dict:
    return full_body(refs["patient"], refs["practitioner"], refs["location"], refs["organization"], refs["appointment"])


def _ids(bundle: dict) -> set[int]:
    return {int(e["resource"]["id"]) for e in bundle.get("entry") or [] if e["search"]["mode"] == "match"}


def _as_user(sub="u-test", org_id="org-test", permissions=ENCOUNTER_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(sub=sub, org_id=org_id, permissions=permissions)


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=encounter_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "Encounter" and data["status"] == "in-progress"
    assert data["class"] == {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB"}


async def test_create_full_round_trip(client, refs):
    body = _full(refs)
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")} == expected
    assert (await client.get(f"{BASE}/{data['id']}")).json() == data


async def test_create_keeps_elements_nothing_searches_on(client, refs):
    """`statusHistory`, `classHistory`, `serviceType`, `priority`, `diagnosis.use/rank`,
    `hospitalization` (apart from specialArrangement) and `location.status/physicalType`
    have no search parameter — they live only in `content`."""
    data = (await client.post(BASE + "/", json=_full(refs))).json()
    assert data["statusHistory"][0]["status"] == "planned"
    assert data["classHistory"][0]["class"]["code"] == "IMP"
    assert data["priority"]["coding"][0]["code"] == "R"
    assert data["diagnosis"][0]["rank"] == 1
    assert data["hospitalization"]["admitSource"] == {"text": "Referral"}
    assert data["location"][0]["status"] == "completed"
    assert data["length"] == {"value": 40, "unit": "min", "system": "http://unitsofmeasure.org", "code": "min"}


async def test_every_status_is_accepted_with_its_real_fhir_spelling(client):
    for status in ALL_STATUSES:
        resp = await client.post(BASE + "/", json=encounter_body(status))
        assert resp.status_code == 201, (status, resp.text)
        assert resp.json()["status"] == status


async def test_create_bad_status_rejected(client):
    for bad in ("in_progress", "IN-PROGRESS", "entered_in_error", "broken"):
        resp = await client.post(BASE + "/", json=encounter_body(bad))
        assert resp.status_code == 422, bad


async def test_create_class_is_a_coding_not_a_codeable_concept(client):
    """R4 Encounter.class is a bare Coding; a CodeableConcept-shaped value is invalid."""
    bad = encounter_body(**{"class": {"coding": [{"code": "AMB"}]}})
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_bad_location_status_and_comparator_rejected(client):
    bad_location = encounter_body(location=[{"location": {"reference": "Location/1"}, "status": "broken"}])
    assert (await client.post(BASE + "/", json=bad_location)).status_code == 422
    bad_length = encounter_body(length={"value": 1, "comparator": "!="})
    assert (await client.post(BASE + "/", json=bad_length)).status_code == 422


async def test_create_ignores_server_managed_id_and_meta(client):
    body = encounter_body(id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_non_fhir_key_rejected(client, native_validation):
    assert (await client.post(BASE + "/", json=encounter_body(not_a_fhir_element=1))).status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in ({"class_code": "AMB"}, {"subject_id": 1}, {"org_id": "x"}):
        resp = await client.post(BASE + "/", json={**encounter_body(), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    assert (await client.post(BASE + "/", json=encounter_body(resourceType="Patient"))).status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=encounter_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


@pytest.mark.parametrize(
    "element,value",
    [
        ("subject", {"reference": "Patient/999999"}),
        ("partOf", {"reference": "Encounter/999999"}),
        ("serviceProvider", {"reference": "Organization/999999"}),
        ("appointment", [{"reference": "Appointment/999999"}]),
        ("participant", [{"individual": {"reference": "Practitioner/999999"}}]),
        ("participant", [{"individual": {"reference": "PractitionerRole/999999"}}]),
        ("location", [{"location": {"reference": "Location/999999"}}]),
        ("hospitalization", {"origin": {"reference": "Location/999999"}}),
        ("hospitalization", {"destination": {"reference": "Organization/999999"}}),
        ("identifier", [{"value": "1", "assigner": {"reference": "Organization/999999"}}]),
    ],
)
async def test_create_local_references_must_exist(client, element, value):
    resp = await client.post(BASE + "/", json=encounter_body(**{element: value}))
    assert resp.status_code == 422, (element, resp.text)


async def test_create_references_that_exist(client, refs):
    role = await create_practitioner_role(client)
    parent = await create_encounter(client, encounter_body())
    body = encounter_body(
        subject={"reference": f"Patient/{refs['patient']}"},
        partOf={"reference": f"Encounter/{parent}"},
        serviceProvider={"reference": f"Organization/{refs['organization']}"},
        appointment=[{"reference": f"Appointment/{refs['appointment']}"}],
        participant=[
            {"individual": {"reference": f"Practitioner/{refs['practitioner']}"}},
            {"individual": {"reference": f"PractitionerRole/{role}"}},
        ],
        location=[{"location": {"reference": f"Location/{refs['location']}"}}],
        hospitalization={
            "origin": {"reference": f"Location/{refs['location']}"},
            "destination": {"reference": f"Organization/{refs['organization']}"},
        },
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    resp = await client.post(BASE + "/", json=encounter_body(subject={"reference": f"Patient/{theirs}"}))
    assert resp.status_code == 422


async def test_create_unmodeled_targets_are_not_checked(client):
    """Group, Account, EpisodeOfCare, ServiceRequest, Condition ... are not resources on
    this server: stored as sent."""
    body = encounter_body(
        subject={"reference": "Group/5"},
        episodeOfCare=[{"reference": "EpisodeOfCare/5"}],
        basedOn=[{"reference": "ServiceRequest/5"}],
        account=[{"reference": "Account/5"}],
        reasonReference=[{"reference": "Condition/5"}, {"reference": "Observation/5"}],
        diagnosis=[{"condition": {"reference": "Procedure/5"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_related_person_participant_must_exist(client, refs):
    body = encounter_body(participant=[{"individual": {"reference": "RelatedPerson/999999"}}])
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    rp = await client.post(
        "/api/fhir/v1/related-persons/", json={"patient": {"reference": f"Patient/{refs['patient']}"}}
    )
    assert rp.status_code == 201, rp.text
    body = encounter_body(participant=[{"individual": {"reference": f"RelatedPerson/{rp.json()['id']}"}}])
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_identifier_assigner_that_exists(client, refs):
    body = encounter_body(identifier=[{"value": "1", "assigner": {"reference": f"Organization/{refs['organization']}"}}])
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/1"
    resp = await client.post(BASE + "/", json=encounter_body(subject={"reference": absolute}))
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": absolute}
    logical = {"identifier": {"system": "urn:pts", "value": "P-9"}, "display": "External"}
    resp = await client.post(BASE + "/", json=encounter_body(subject=logical))
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == logical


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, refs):
    encounter = await create_encounter(client, _full(refs))
    resp = await client.get(f"{BASE}/{encounter}")
    assert resp.status_code == 200 and resp.json()["id"] == str(encounter)


async def test_get_is_fhir_regardless_of_accept(client):
    encounter = await create_encounter(client, encounter_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{encounter}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Encounter"


async def test_xml_only_accept_is_406(client):
    encounter = await create_encounter(client, encounter_body())
    resp = await client.get(f"{BASE}/{encounter}", headers={"Accept": "application/fhir+xml"})
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, refs):
    encounter = await create_encounter(client, _full(refs))
    resp = await client.patch(
        f"{BASE}/{encounter}", json={"status": "finished", "period": {"start": START, "end": "2026-06-01T10:00:00Z"}}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "finished" and resp.json()["period"]["end"] == "2026-06-01T10:00:00Z"
    assert resp.json()["subject"]["reference"] == f"Patient/{refs['patient']}"  # untouched
    assert resp.json()["class"]["code"] == "AMB"
    assert resp.json()["hospitalization"]["admitSource"] == {"text": "Referral"}


async def test_patch_reindexes_search(client, refs):
    encounter = await create_encounter(client, _full(refs))
    await client.patch(f"{BASE}/{encounter}", json={"status": "finished"})
    assert encounter not in _ids((await client.get(BASE + "/", params={"status": "in-progress"})).json())
    assert encounter in _ids((await client.get(BASE + "/", params={"status": "finished"})).json())


async def test_patch_class_replaced_and_reindexed(client):
    encounter = await create_encounter(client, encounter_body(class_code="AMB"))
    resp = await client.patch(f"{BASE}/{encounter}", json={"class": {"system": "http://x", "code": "EMER"}})
    assert resp.status_code == 200, resp.text
    assert encounter not in _ids((await client.get(BASE + "/", params={"class": "AMB"})).json())
    assert encounter in _ids((await client.get(BASE + "/", params={"class": "http://x|EMER"})).json())


async def test_patch_subject_replaced_and_cleared(client, refs):
    encounter = await create_encounter(client, encounter_body(subject={"reference": f"Patient/{refs['patient']}"}))
    other = await create_patient(client)
    resp = await client.patch(f"{BASE}/{encounter}", json={"subject": {"reference": f"Patient/{other}"}})
    assert resp.status_code == 200, resp.text
    assert encounter not in _ids((await client.get(BASE + "/", params={"patient": str(refs["patient"])})).json())
    assert encounter in _ids((await client.get(BASE + "/", params={"patient": str(other)})).json())
    resp = await client.patch(f"{BASE}/{encounter}", json={"subject": None})
    assert "subject" not in resp.json()
    assert encounter not in _ids((await client.get(BASE + "/", params={"patient": str(other)})).json())


async def test_patch_replaces_lists_and_empty_clears(client, refs):
    encounter = await create_encounter(
        client,
        _full(refs) | {"identifier": [{"system": "urn:e", "value": "E-77"}], "type": [{"coding": [{"code": "x1"}]}]},
    )
    assert encounter in _ids((await client.get(BASE + "/", params={"identifier": "E-77"})).json())
    resp = await client.patch(f"{BASE}/{encounter}", json={"identifier": [], "participant": [], "location": []})
    for gone in ("identifier", "participant", "location"):
        assert gone not in resp.json()
    assert resp.json()["type"] == [{"coding": [{"code": "x1"}]}]  # untouched
    assert encounter not in _ids((await client.get(BASE + "/", params={"identifier": "E-77"})).json())
    assert encounter not in _ids(
        (await client.get(BASE + "/", params={"practitioner": str(refs["practitioner"])})).json()
    )
    assert encounter not in _ids((await client.get(BASE + "/", params={"location": str(refs["location"])})).json())


async def test_patch_participant_location_and_appointment_reindex(client, refs):
    encounter = await create_encounter(client, _full(refs))
    other = await create_practitioner(client)
    await client.patch(f"{BASE}/{encounter}", json={"participant": [{"individual": {"reference": f"Practitioner/{other}"}}]})
    assert encounter not in _ids((await client.get(BASE + "/", params={"practitioner": str(refs["practitioner"])})).json())
    assert encounter in _ids((await client.get(BASE + "/", params={"practitioner": str(other)})).json())
    # participant.type was replaced with the participant, so `participant-type` no longer finds it
    assert encounter not in _ids((await client.get(BASE + "/", params={"participant-type": "ATND"})).json())


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client, refs):
    encounter = await create_encounter(client, encounter_body(subject={"reference": f"Patient/{refs['patient']}"}))
    resp = await client.patch(f"{BASE}/{encounter}", json={"subject": {"reference": "Patient/999999"}})
    assert resp.status_code == 422
    assert (await client.get(f"{BASE}/{encounter}")).json()["subject"] == {"reference": f"Patient/{refs['patient']}"}


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    encounter = await create_encounter(client, encounter_body())
    assert (await client.patch(f"{BASE}/{encounter}", json={"status": "broken"})).status_code == 422
    assert (await client.get(f"{BASE}/{encounter}")).json()["status"] == "in-progress"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "finished"})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, refs):
    encounter = await create_encounter(
        client, _full(refs) | {"identifier": [{"system": "urn:e", "value": "E-88"}]}
    )
    assert (await client.delete(f"{BASE}/{encounter}")).status_code == 204
    assert (await client.get(f"{BASE}/{encounter}")).status_code == 404
    # Its index rows are gone with it.
    assert encounter not in _ids((await client.get(BASE + "/", params={"identifier": "E-88"})).json())
    assert encounter not in _ids((await client.get(BASE + "/", params={"patient": str(refs["patient"])})).json())
    assert encounter not in _ids((await client.get(BASE + "/", params={"location": str(refs["location"])})).json())


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client):
    _as_user(permissions=["encounter:read"])
    assert (await client.post(BASE + "/", json=encounter_body())).status_code == 403


async def test_org_less_token_rejected(client):
    encounter = await create_encounter(client, encounter_body())

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": ENCOUNTER_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=encounter_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{encounter}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    encounter = await create_encounter(client, encounter_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{encounter}"),
            await other_client.patch(f"{BASE}/{encounter}", json={"status": "finished"}),
            await other_client.delete(f"{BASE}/{encounter}"),
        ):
            assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_encounter(client, encounter_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]))
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})).json()
        assert bundle["total"] == 0
    finally:
        _as_user()

"""Core medication dispense endpoint coverage.

MedicationDispense is stored whole in `content` (like MedicationAdministration, MedicationStatement
and the other content-based resources): the request body (genuine FHIR R4 MedicationDispense JSON)
is validated and stored in `content`, every response is FHIR R4 (`application/fhir+json`,
regardless of Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/medicationdispense.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`subject`, `context`,
`medicationReference`, `performer.actor`, `location`, `authorizingPrescription`, `destination`,
`receiver`, `substitution.responsibleParty`, `partOf`, `supportingInformation`, a note author and
every identifier's `assigner`). Search lives in test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.medication_dispense.conftest import DISPENSE_PERMS
from tests.integration.medication_dispense.support import (
    BASE,
    create_encounter,
    create_episode,
    create_group,
    create_location,
    create_medication,
    create_medication_dispense,
    create_medication_request,
    create_observation,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_procedure,
    create_related_person,
    encounter_body,
    episode_body,
    full_body,
    group_body,
    medication_body,
    medication_dispense_body,
    medication_request_body,
    observation_body,
    procedure_body,
    related_person_body,
)


@pytest.fixture
def native_validation(monkeypatch):
    """The base R4 validator may be switched off in configs/config.yaml; tests that assert "a key
    that isn't FHIR is a 422" need it on: the project's own structural check."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=DISPENSE_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client, with_medication_reference=False) -> tuple[int, dict]:
    organization = await create_organization(client)
    patient = await create_patient(client)
    practitioner = await create_practitioner(client)
    encounter = await create_encounter(client, encounter_body())
    observation = await create_observation(client, observation_body(patient))
    request = await create_medication_request(client, medication_request_body(patient))
    location = await create_location(client)
    medication = (
        await create_medication(client, medication_body())
        if with_medication_reference
        else None
    )
    body = full_body(
        organization,
        patient,
        practitioner,
        encounter,
        observation,
        request,
        location,
        medication,
    )
    return await create_medication_dispense(client, body), body


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=medication_dispense_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    assert resp.json()["resourceType"] == "MedicationDispense"
    assert resp.json()["id"] == "590000"  # the first id of the block


async def test_create_full_round_trip_including_dosage_and_substitution(client):
    dispense, body = await _full(client)
    data = (await client.get(f"{BASE}/{dispense}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_with_a_medication_reference(client):
    dispense, body = await _full(client, with_medication_reference=True)
    data = (await client.get(f"{BASE}/{dispense}")).json()
    assert data["medicationReference"] == body["medicationReference"]
    assert "medicationCodeableConcept" not in data


async def test_create_status_reason_choice_round_trips(client):
    coded = await create_medication_dispense(
        client,
        medication_dispense_body(
            status="cancelled", statusReasonCodeableConcept={"text": "Out of stock"}
        ),
    )
    assert (await client.get(f"{BASE}/{coded}")).json()[
        "statusReasonCodeableConcept"
    ] == {"text": "Out of stock"}
    referenced = await create_medication_dispense(
        client,
        medication_dispense_body(
            status="cancelled",
            statusReasonReference={
                "reference": "https://other.example.org/fhir/DetectedIssue/1"
            },
        ),
    )
    assert (await client.get(f"{BASE}/{referenced}")).json()[
        "statusReasonReference"
    ] == {"reference": "https://other.example.org/fhir/DetectedIssue/1"}


@pytest.mark.parametrize(
    "status",
    [
        "preparation",
        "in-progress",
        "cancelled",
        "on-hold",
        "completed",
        "entered-in-error",
        "stopped",
        "declined",
        "unknown",
    ],
)
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=medication_dispense_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_ignores_server_managed_id_and_meta(client):
    body = medication_dispense_body(
        id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "bogus"},
        {"status": "in_progress"},
        {"identifier": {"value": "x"}},
        {"partOf": {"reference": "Procedure/1"}},
        {"partOf": ["Procedure/1"]},
        {"category": [{"text": "x"}]},
        {"subject": "Patient/1"},
        {"context": "Encounter/1"},
        {"supportingInformation": {"reference": "x"}},
        {"performer": {"actor": {"reference": "Practitioner/1"}}},
        {"performer": ["x"]},
        {"location": [{"reference": "Location/1"}]},
        {"authorizingPrescription": {"reference": "MedicationRequest/1"}},
        {"type": [{"text": "x"}]},
        {"quantity": "30"},
        {"whenPrepared": 5},
        {"whenHandedOver": 5},
        {"destination": [{"reference": "Location/1"}]},
        {"receiver": {"reference": "Patient/1"}},
        {"note": {"text": "x"}},
        {"note": ["x"]},
        {"dosageInstruction": {"text": "x"}},
        {"dosageInstruction": ["x"]},
        {"substitution": [{"wasSubstituted": True}]},
        {"substitution": {"responsibleParty": {"reference": "Practitioner/1"}}},
        {"detectedIssue": {"reference": "DetectedIssue/1"}},
        {"eventHistory": {"reference": "Provenance/1"}},
    ):
        resp = await client.post(BASE + "/", json=medication_dispense_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(
        BASE + "/", json=medication_dispense_body(not_a_fhir_element=1)
    )
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in (
        {"subject_id": 1},
        {"org_id": "x"},
        {"user_id": "x"},
        {"when_prepared": "2026-01-01"},
        {"substitution_was_substituted": True},
    ):
        resp = await client.post(
            BASE + "/", json={**medication_dispense_body(), **stale}
        )
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(
        BASE + "/", json=medication_dispense_body(resourceType="Patient")
    )
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=medication_dispense_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_subject_must_exist_patient_or_group(client):
    patient = await create_patient(client)
    group = await create_group(client, group_body(type="person"))
    for ref in (f"Patient/{patient}", f"Group/{group}"):
        body = medication_dispense_body(subject={"reference": ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for ref in ("Patient/999999", "Group/999999"):
        body = medication_dispense_body(subject={"reference": ref})
        resp = await client.post(BASE + "/", json=body)
        assert resp.status_code == 422 and "subject" in resp.text, ref


async def test_create_context_must_exist(client):
    encounter = await create_encounter(client, encounter_body())
    patient = await create_patient(client)
    episode = await create_episode(client, episode_body(patient))
    for ref in (f"Encounter/{encounter}", f"EpisodeOfCare/{episode}"):
        body = medication_dispense_body(context={"reference": ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for ref in ("Encounter/999999", "EpisodeOfCare/999999"):
        body = medication_dispense_body(context={"reference": ref})
        resp = await client.post(BASE + "/", json=body)
        assert resp.status_code == 422 and "context" in resp.text, ref


async def test_create_performer_actor_must_exist(client):
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    patient = await create_patient(client)
    related = await create_related_person(client, related_person_body(patient))
    role = await create_practitioner_role(
        client, {"practitioner": {"reference": f"Practitioner/{practitioner}"}}
    )
    for ref in (
        f"Practitioner/{practitioner}",
        f"PractitionerRole/{role}",
        f"Organization/{organization}",
        f"Patient/{patient}",
        f"RelatedPerson/{related}",
        "Device/12",
    ):
        body = medication_dispense_body(performer=[{"actor": {"reference": ref}}])
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    bad = medication_dispense_body(
        performer=[{"actor": {"reference": "Practitioner/999999"}}]
    )
    resp = await client.post(BASE + "/", json=bad)
    assert resp.status_code == 422 and "performer[0].actor" in resp.text


async def test_create_location_destination_prescription_receiver_must_exist(client):
    location = await create_location(client)
    patient = await create_patient(client)
    practitioner = await create_practitioner(client)
    request = await create_medication_request(client, medication_request_body(patient))
    ok = medication_dispense_body(
        location={"reference": f"Location/{location}"},
        destination={"reference": f"Location/{location}"},
        authorizingPrescription=[{"reference": f"MedicationRequest/{request}"}],
        receiver=[
            {"reference": f"Patient/{patient}"},
            {"reference": f"Practitioner/{practitioner}"},
        ],
        substitution={
            "wasSubstituted": True,
            "responsibleParty": [{"reference": f"Practitioner/{practitioner}"}],
        },
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for element, value, path in (
        ("location", {"reference": "Location/999999"}, "location"),
        ("destination", {"reference": "Location/999999"}, "destination"),
        (
            "authorizingPrescription",
            [{"reference": "MedicationRequest/999999"}],
            "authorizingPrescription[0]",
        ),
        ("receiver", [{"reference": "Patient/999999"}], "receiver[0]"),
        (
            "substitution",
            {
                "wasSubstituted": True,
                "responsibleParty": [{"reference": "Practitioner/999999"}],
            },
            "substitution.responsibleParty[0]",
        ),
    ):
        resp = await client.post(
            BASE + "/", json=medication_dispense_body(**{element: value})
        )
        assert resp.status_code == 422 and path in resp.text, (element, resp.text)


async def test_create_medication_reference_must_exist(client):
    medication = await create_medication(client, medication_body())
    base = {
        "status": "completed",
        "subject": {"reference": "https://other.example.org/fhir/Patient/1"},
    }
    ok = {**base, "medicationReference": {"reference": f"Medication/{medication}"}}
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = {**base, "medicationReference": {"reference": "Medication/999999"}}
    resp = await client.post(BASE + "/", json=bad)
    assert resp.status_code == 422 and "medicationReference" in resp.text


async def test_create_part_of_and_support_must_exist(client):
    patient = await create_patient(client)
    procedure = await create_procedure(client, procedure_body(patient))
    observation = await create_observation(client, observation_body(patient))
    ok = medication_dispense_body(
        partOf=[{"reference": f"Procedure/{procedure}"}],
        supportingInformation=[{"reference": f"Observation/{observation}"}],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for element, ref in (
        ("partOf", "Procedure/999999"),
        ("supportingInformation", "Observation/999999"),
    ):
        resp = await client.post(
            BASE + "/",
            json=medication_dispense_body(**{element: [{"reference": ref}]}),
        )
        assert resp.status_code == 422 and f"{element}[0]" in resp.text, (element, ref)


async def test_create_note_author_and_identifier_assigner_must_exist(client):
    practitioner = await create_practitioner(client)
    ok = medication_dispense_body(
        note=[
            {
                "text": "n",
                "authorReference": {"reference": f"Practitioner/{practitioner}"},
            }
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = medication_dispense_body(
        note=[{"text": "n", "authorReference": {"reference": "Practitioner/999999"}}]
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422
    bad = medication_dispense_body(
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}]
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    body = medication_dispense_body(theirs)
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_absolute_logical_and_unmodeled_references_not_resolved(client):
    """An absolute URL, a logical (identifier-only) reference and a type this server does not
    have are stored as sent."""
    body = medication_dispense_body(
        subject={"reference": "https://other.example.org/fhir/Patient/1"},
        context={"identifier": {"system": "urn:enc", "value": "E-9"}},
        performer=[{"actor": {"reference": "Device/12"}}],
        eventHistory=[{"reference": "Provenance/270001"}],
        authorizingPrescription=[
            {"reference": "https://other.example.org/fhir/MedicationRequest/9"}
        ],
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["subject"]["reference"] == "https://other.example.org/fhir/Patient/1"
    assert data["context"]["identifier"]["value"] == "E-9"
    assert data["performer"][0]["actor"]["reference"] == "Device/12"
    assert data["eventHistory"][0]["reference"] == "Provenance/270001"


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    dispense, _ = await _full(client)
    resp = await client.get(f"{BASE}/{dispense}")
    assert resp.status_code == 200 and resp.json()["id"] == str(dispense)


async def test_get_is_fhir_regardless_of_accept(client):
    dispense = await create_medication_dispense(client, medication_dispense_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{dispense}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "MedicationDispense"


async def test_xml_only_accept_is_406(client):
    dispense = await create_medication_dispense(client, medication_dispense_body())
    resp = await client.get(
        f"{BASE}/{dispense}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    dispense, body = await _full(client)
    resp = await client.patch(f"{BASE}/{dispense}", json={"status": "stopped"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "stopped"
    assert resp.json()["dosageInstruction"] == body["dosageInstruction"]  # untouched
    assert resp.json()["substitution"] == body["substitution"]


async def test_patch_reindexes_search(client):
    dispense, _ = await _full(client)
    patient = await create_patient(client)
    await client.patch(
        f"{BASE}/{dispense}",
        json={
            "status": "stopped",
            "whenPrepared": "2030-05-06T07:08:09Z",
            "subject": {"reference": f"Patient/{patient}"},
            "type": {"coding": [{"system": "http://example.org/types", "code": "TF"}]},
            "receiver": [],
        },
    )
    for param, old, new in (
        ("status", "completed", "stopped"),
        ("whenprepared", "lt2027-01-01", "ge2030-01-01"),
        ("type", "FF", "TF"),
        ("patient", None, str(patient)),
    ):
        if old is not None:
            assert dispense not in _ids(
                (await client.get(BASE + "/", params={param: old})).json()
            ), param
        assert dispense in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param
    assert dispense in _ids(
        (await client.get(BASE + "/", params={"receiver:missing": "true"})).json()
    )


async def test_patch_replaces_the_dosage_list(client):
    dispense, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{dispense}", json={"dosageInstruction": [{"text": "only"}]}
    )
    assert resp.json()["dosageInstruction"] == [{"text": "only"}]
    cleared = await client.patch(f"{BASE}/{dispense}", json={"dosageInstruction": []})
    assert "dosageInstruction" not in cleared.json()
    assert cleared.json()["status"] == "completed"  # untouched


async def test_patch_clears_destination_and_missing_follows(client):
    location = await create_location(client)
    dispense = await create_medication_dispense(
        client,
        medication_dispense_body(destination={"reference": f"Location/{location}"}),
    )
    resp = await client.patch(f"{BASE}/{dispense}", json={"destination": None})
    assert "destination" not in resp.json()
    assert dispense in _ids(
        (await client.get(BASE + "/", params={"destination:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    dispense = await create_medication_dispense(client, medication_dispense_body())
    resp = await client.patch(
        f"{BASE}/{dispense}",
        json={"performer": [{"actor": {"reference": "Practitioner/999999"}}]},
    )
    assert resp.status_code == 422
    assert "performer" not in (await client.get(f"{BASE}/{dispense}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    dispense = await create_medication_dispense(
        client, medication_dispense_body(status="completed")
    )
    assert (
        await client.patch(f"{BASE}/{dispense}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{dispense}")).json()["status"] == "completed"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "stopped"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    dispense, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{dispense}")).status_code == 204
    assert (await client.get(f"{BASE}/{dispense}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "MD-1001"),
        ("status", "completed"),
        ("code", "197361"),
        ("type", "FF"),
    ):
        assert dispense not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["medication_dispense:read"])
    assert (
        await client.post(BASE + "/", json=medication_dispense_body())
    ).status_code == 403


async def test_org_less_token_rejected(client):
    dispense = await create_medication_dispense(client, medication_dispense_body())

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": DISPENSE_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (
        await client.post(BASE + "/", json=medication_dispense_body())
    ).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{dispense}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    dispense = await create_medication_dispense(client, medication_dispense_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{dispense}"),
            await other_client.patch(f"{BASE}/{dispense}", json={"status": "stopped"}),
            await other_client.delete(f"{BASE}/{dispense}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_medication_dispense(
        client,
        medication_dispense_body(
            identifier=[{"system": "urn:t", "value": "TenantAOnly"}]
        ),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


# -- Other resources that point at a dispense -------------------------------------------------


async def test_a_dispense_is_checked_where_a_reference_can_name_it(client):
    """Observation.partOf and MedicationStatement.partOf can name a MedicationDispense: it must
    exist now that dispenses are a resource here."""
    patient = await create_patient(client)
    dispense = await create_medication_dispense(
        client, medication_dispense_body(patient)
    )
    observations = "/api/fhir/v1/observations"
    ok = observation_body(
        patient, partOf=[{"reference": f"MedicationDispense/{dispense}"}]
    )
    assert (await client.post(observations + "/", json=ok)).status_code == 201
    bad = observation_body(patient, partOf=[{"reference": "MedicationDispense/999999"}])
    resp = await client.post(observations + "/", json=bad)
    assert resp.status_code == 422 and "partOf" in resp.text

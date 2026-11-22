"""Core medication request endpoint coverage.

MedicationRequest is stored Medplum-style (like Patient, Encounter, Condition, Procedure,
ServiceRequest, Medication and the other content-based resources): the request body (genuine
FHIR R4 MedicationRequest JSON) is validated and stored whole in `content`, every response is
FHIR R4 (`application/fhir+json`, regardless of Accept), and only the FHIR R4 search parameters
are indexed (https://www.hl7.org/fhir/R4/medicationrequest.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference. Search lives in test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.medication_request.conftest import MEDICATION_REQUEST_PERMS
from tests.integration.medication_request.support import (
    BASE,
    RXNORM,
    SCT,
    concept,
    create_condition,
    create_detected_issue,
    create_encounter,
    create_medication,
    create_medication_request,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_related_person,
    encounter_body,
    full_body,
    medication_body,
    medication_request_body,
    related_person_body,
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


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=MEDICATION_REQUEST_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client, patient) -> tuple[int, dict]:
    encounter = await create_encounter(
        client, encounter_body(subject={"reference": f"Patient/{patient}"})
    )
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    medication = await create_medication(client, medication_body(status="active"))
    prior = await create_medication_request(client, medication_request_body(patient))
    condition = await create_condition(client, patient)
    issue = await create_detected_issue(client, patient)
    body = full_body(
        patient,
        encounter,
        practitioner,
        organization,
        medication,
        prior,
        condition,
        issue,
    )
    return await create_medication_request(client, body), body


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client, patient):
    resp = await client.post(BASE + "/", json=medication_request_body(patient))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "MedicationRequest"
    assert data["status"] == "active" and data["intent"] == "order"
    assert data["subject"] == {"reference": f"Patient/{patient}"}


async def test_create_full_round_trip(client, patient):
    medication_request, body = await _full(client, patient)
    data = (await client.get(f"{BASE}/{medication_request}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client, patient):
    """`statusReason`, `reported[x]`, `dispenseRequest` (apart from its performer),
    `substitution`, `dosageInstruction`, `groupIdentifier`, `insurance` and `eventHistory` live
    only in `content`."""
    medication_request, _ = await _full(client, patient)
    data = (await client.get(f"{BASE}/{medication_request}")).json()
    assert data["statusReason"]["coding"][0]["code"] == "1"
    assert data["reportedBoolean"] is True
    assert data["groupIdentifier"]["value"] == "GRP-1"
    assert data["dispenseRequest"]["numberOfRepeatsAllowed"] == 2
    assert data["dispenseRequest"]["quantity"]["value"] == 60
    assert data["substitution"]["allowedBoolean"] is True
    assert data["dosageInstruction"][0]["doseAndRate"][0]["doseQuantity"]["value"] == 1
    assert data["insurance"] == [{"reference": "Coverage/240001"}]
    assert data["eventHistory"] == [{"reference": "Provenance/270001"}]


@pytest.mark.parametrize(
    "extra",
    [
        {"medicationCodeableConcept": {"text": "Aspirin"}},
        {
            "medicationReference": {
                "reference": "https://other.example.org/Medication/1"
            }
        },
    ],
    ids=["codeableConcept", "reference"],
)
async def test_create_each_medication_choice_round_trips(client, patient, extra):
    body = medication_request_body(patient)
    del body["medicationCodeableConcept"]
    body.update(extra)
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    for key, value in extra.items():
        assert resp.json()[key] == value


@pytest.mark.parametrize(
    "extra",
    [
        {"reportedBoolean": True},
        {
            "reportedReference": {
                "reference": "https://other.example.org/fhir/Patient/1"
            }
        },
    ],
    ids=["boolean", "reference"],
)
async def test_create_each_reported_choice_round_trips(client, extra):
    resp = await client.post(BASE + "/", json=medication_request_body(**extra))
    assert resp.status_code == 201, resp.text
    for key, value in extra.items():
        assert resp.json()[key] == value


@pytest.mark.parametrize(
    "substitution",
    [
        {"allowedBoolean": False},
        {"allowedCodeableConcept": {"text": "generic"}, "reason": {"text": "cost"}},
    ],
    ids=["boolean", "codeableConcept"],
)
async def test_create_each_substitution_choice_round_trips(
    client, patient, substitution
):
    resp = await client.post(
        BASE + "/", json=medication_request_body(patient, substitution=substitution)
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["substitution"] == substitution


@pytest.mark.parametrize(
    "status",
    [
        "active",
        "on-hold",
        "cancelled",
        "completed",
        "entered-in-error",
        "stopped",
        "draft",
        "unknown",
    ],
)
async def test_create_every_status_round_trips(client, patient, status):
    resp = await client.post(
        BASE + "/", json=medication_request_body(patient, status=status)
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


@pytest.mark.parametrize(
    "intent",
    [
        "proposal",
        "plan",
        "order",
        "original-order",
        "reflex-order",
        "filler-order",
        "instance-order",
        "option",
    ],
)
async def test_create_every_intent_round_trips(client, patient, intent):
    resp = await client.post(
        BASE + "/", json=medication_request_body(patient, intent=intent)
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["intent"] == intent


@pytest.mark.parametrize("priority", ["routine", "urgent", "asap", "stat"])
async def test_create_every_priority_round_trips(client, patient, priority):
    resp = await client.post(
        BASE + "/", json=medication_request_body(patient, priority=priority)
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["priority"] == priority


async def test_create_ignores_server_managed_id_and_meta(client, patient):
    body = medication_request_body(
        patient, id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client, patient):
    for bad in (
        {"status": "robot"},
        {"intent": "robot"},
        {"priority": "robot"},
        {"authoredOn": "yesterday"},
        {"category": concept(SCT, "1")},
        {"medicationCodeableConcept": "x"},
        {"identifier": {"value": "x"}},
        {"groupIdentifier": [{"value": "x"}]},
        {"basedOn": {"reference": "MedicationRequest/1"}},
        {"note": {"text": "x"}},
        {"doNotPerform": "yes"},
        {"requester": "Practitioner/1"},
        {"performer": [{"reference": "Practitioner/1"}]},
        {"dosageInstruction": {"text": "x"}},
        {"dispenseRequest": "x"},
        {"dispenseRequest": {"numberOfRepeatsAllowed": -1}},
        {"substitution": "x"},
        {"priorPrescription": [{"reference": "MedicationRequest/1"}]},
        {"instantiatesUri": "http://x"},
    ):
        resp = await client.post(
            BASE + "/", json=medication_request_body(patient, **bad)
        )
        assert resp.status_code == 422, (bad, resp.text)
    resp = await client.post(
        BASE + "/",
        json={
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {"text": "x"},
            "subject": "Patient/1",
        },
    )
    assert resp.status_code == 422


async def test_create_non_fhir_key_rejected(client, patient, native_validation):
    resp = await client.post(
        BASE + "/", json=medication_request_body(patient, not_a_fhir_element=1)
    )
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, patient, native_validation):
    for stale in (
        {"medication_codeable_concept_text": "x"},
        {"authored_on": "2020-01-01"},
        {"org_id": "x"},
    ):
        resp = await client.post(
            BASE + "/", json={**medication_request_body(patient), **stale}
        )
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, patient):
    resp = await client.post(
        BASE + "/", json=medication_request_body(patient, resourceType="Patient")
    )
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client, patient):
    data = (await client.post(BASE + "/", json=medication_request_body(patient))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_patient_subject_must_exist(client):
    assert (
        await client.post(BASE + "/", json=medication_request_body(999999))
    ).status_code == 422


async def test_create_subject_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert (
        await client.post(BASE + "/", json=medication_request_body(theirs))
    ).status_code == 422


async def test_create_group_subject_is_not_checked(client):
    body = medication_request_body()
    body["subject"] = {"reference": "Group/999999"}
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": "Group/999999"}


async def test_create_encounter_must_exist(client, patient):
    encounter = await create_encounter(
        client, encounter_body(subject={"reference": f"Patient/{patient}"})
    )
    ok = medication_request_body(
        patient, encounter={"reference": f"Encounter/{encounter}"}
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = medication_request_body(
        patient, encounter={"reference": "Encounter/999999"}
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_medication_reference_must_exist(client, patient):
    medication = await create_medication(client, medication_body())
    body = medication_request_body(patient)
    del body["medicationCodeableConcept"]
    ok = {**body, "medicationReference": {"reference": f"Medication/{medication}"}}
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = {**body, "medicationReference": {"reference": "Medication/999999"}}
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_requester_performer_recorder_reporter_must_exist(client, patient):
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(client)
    organization = await create_organization(client)
    related = await create_related_person(client, related_person_body(patient))
    for ref in (
        f"Practitioner/{practitioner}",
        f"PractitionerRole/{role}",
        f"Organization/{organization}",
        f"Patient/{patient}",
        f"RelatedPerson/{related}",
    ):
        for element in ("requester", "performer"):
            body = medication_request_body(patient, **{element: {"reference": ref}})
            assert (await client.post(BASE + "/", json=body)).status_code == 201, (
                element,
                ref,
            )
        body = medication_request_body(patient, reportedReference={"reference": ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for element in ("requester", "performer", "reportedReference"):
        for missing in (
            "Practitioner/999999",
            "Organization/999999",
            "RelatedPerson/999999",
        ):
            body = medication_request_body(patient, **{element: {"reference": missing}})
            assert (await client.post(BASE + "/", json=body)).status_code == 422, (
                element,
                missing,
            )
    for good, bad in (
        (f"Practitioner/{practitioner}", "Practitioner/999999"),
        (f"PractitionerRole/{role}", "PractitionerRole/999999"),
    ):
        ok = medication_request_body(patient, recorder={"reference": good})
        assert (await client.post(BASE + "/", json=ok)).status_code == 201
        nope = medication_request_body(patient, recorder={"reference": bad})
        assert (await client.post(BASE + "/", json=nope)).status_code == 422


async def test_create_unmodeled_requesters_and_performers_not_checked(client, patient):
    body = medication_request_body(
        patient,
        requester={"reference": "Device/999999"},
        performer={"reference": "CareTeam/999999"},
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_dispenser_must_exist(client, patient):
    organization = await create_organization(client)
    ok = medication_request_body(
        patient,
        dispenseRequest={"performer": {"reference": f"Organization/{organization}"}},
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = medication_request_body(
        patient, dispenseRequest={"performer": {"reference": "Organization/999999"}}
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_based_on_and_prior_prescription_must_exist(client, patient):
    first = await create_medication_request(client, medication_request_body(patient))
    ok = medication_request_body(
        patient,
        basedOn=[{"reference": f"MedicationRequest/{first}"}],
        priorPrescription={"reference": f"MedicationRequest/{first}"},
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for body in (
        medication_request_body(
            patient, basedOn=[{"reference": "MedicationRequest/999999"}]
        ),
        medication_request_body(
            patient, basedOn=[{"reference": "ServiceRequest/999999"}]
        ),
        medication_request_body(
            patient, basedOn=[{"reference": "ImmunizationRecommendation/999999"}]
        ),
        medication_request_body(
            patient, priorPrescription={"reference": "MedicationRequest/999999"}
        ),
    ):
        assert (await client.post(BASE + "/", json=body)).status_code == 422, body


async def test_create_care_plan_based_on_must_exist(client, patient):
    from tests.helpers.care_plans import create_minimal_care_plan

    plan = await create_minimal_care_plan(client)
    ok = medication_request_body(patient, basedOn=[{"reference": f"CarePlan/{plan}"}])
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = medication_request_body(patient, basedOn=[{"reference": "CarePlan/999999"}])
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_reason_reference_is_checked_for_rebuilt_types(client, patient):
    condition = await create_condition(client, patient)
    ok = medication_request_body(
        patient, reasonReference=[{"reference": f"Condition/{condition}"}]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for missing in ("Condition/999999", "Observation/999999"):
        body = medication_request_body(
            patient, reasonReference=[{"reference": missing}]
        )
        assert (await client.post(BASE + "/", json=body)).status_code == 422, missing


async def test_create_detected_issue_must_exist(client, patient):
    issue = await create_detected_issue(client, patient)
    ok = medication_request_body(
        patient, detectedIssue=[{"reference": f"DetectedIssue/{issue}"}]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = medication_request_body(
        patient, detectedIssue=[{"reference": "DetectedIssue/999999"}]
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_supporting_information_is_checked_for_rebuilt_types(
    client, patient
):
    ok = medication_request_body(
        patient, supportingInformation=[{"reference": f"Patient/{patient}"}]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = medication_request_body(
        patient, supportingInformation=[{"reference": "Observation/999999"}]
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422
    stored = medication_request_body(
        patient, supportingInformation=[{"reference": "DocumentReference/999999"}]
    )
    assert (await client.post(BASE + "/", json=stored)).status_code == 201


async def test_create_insurance_and_event_history_are_not_checked(client, patient):
    body = medication_request_body(
        patient,
        insurance=[{"reference": "Coverage/999999"}],
        eventHistory=[{"reference": "Provenance/999999"}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_note_author_is_checked(client, patient):
    practitioner = await create_practitioner(client)
    ok = medication_request_body(
        patient,
        note=[
            {
                "text": "n",
                "authorReference": {"reference": f"Practitioner/{practitioner}"},
            }
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = medication_request_body(
        patient,
        note=[{"text": "n", "authorReference": {"reference": "Practitioner/999999"}}],
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_every_identifier_assigner_must_exist(client, patient):
    org = await create_organization(client)
    ok = {"value": "1", "assigner": {"reference": f"Organization/{org}"}}
    missing = {"value": "1", "assigner": {"reference": "Organization/999999"}}
    for good, bad in (
        ({"identifier": [ok]}, {"identifier": [missing]}),
        ({"groupIdentifier": ok}, {"groupIdentifier": missing}),
    ):
        assert (
            await client.post(BASE + "/", json=medication_request_body(patient, **good))
        ).status_code == 201, good
        assert (
            await client.post(BASE + "/", json=medication_request_body(patient, **bad))
        ).status_code == 422, bad


async def test_create_absolute_and_logical_references_not_resolved(client):
    resp = await client.post(BASE + "/", json=medication_request_body())
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {
        "reference": "https://other.example.org/fhir/Patient/1"
    }
    logical = {
        "identifier": {"system": "urn:pts", "value": "P-9"},
        "display": "External",
    }
    body = medication_request_body(
        requester={"reference": "https://other.example.org/fhir/Practitioner/7"},
        basedOn=[{"identifier": {"system": "urn:orders", "value": "O-1"}}],
    )
    body["subject"] = logical
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == logical
    assert resp.json()["basedOn"] == body["basedOn"]


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client, patient):
    medication_request, _ = await _full(client, patient)
    resp = await client.get(f"{BASE}/{medication_request}")
    assert resp.status_code == 200 and resp.json()["id"] == str(medication_request)


async def test_get_is_fhir_regardless_of_accept(client, patient):
    medication_request = await create_medication_request(
        client, medication_request_body(patient)
    )
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{medication_request}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "MedicationRequest"


async def test_xml_only_accept_is_406(client, patient):
    medication_request = await create_medication_request(
        client, medication_request_body(patient)
    )
    resp = await client.get(
        f"{BASE}/{medication_request}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client, patient):
    medication_request, _ = await _full(client, patient)
    resp = await client.patch(
        f"{BASE}/{medication_request}",
        json={
            "status": "completed",
            "priority": "stat",
            "note": [{"text": "Dispensed"}],
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "completed" and resp.json()["priority"] == "stat"
    assert resp.json()["note"] == [{"text": "Dispensed"}]
    assert resp.json()["subject"] == {"reference": f"Patient/{patient}"}  # untouched
    assert resp.json()["intent"] == "order"
    assert resp.json()["dispenseRequest"]["quantity"]["value"] == 60


async def test_patch_reindexes_search(client, patient):
    medication_request, _ = await _full(client, patient)
    await client.patch(
        f"{BASE}/{medication_request}",
        json={
            "status": "stopped",
            "intent": "plan",
            "priority": "routine",
            "authoredOn": "2024-05-01",
            "category": [concept(SCT, "888")],
            "performerType": concept(SCT, "999"),
            "dosageInstruction": [{"timing": {"event": ["2024-06-01T08:00:00Z"]}}],
            "medicationReference": None,
            "medicationCodeableConcept": concept(RXNORM, "9999"),
        },
    )
    for param, old, new in (
        ("status", "active", "stopped"),
        ("intent", "order", "plan"),
        ("priority", "urgent", "routine"),
        ("authoredon", "2023-01-15", "2024-05-01"),
        ("category", "outpatient", "888"),
        ("intended-performertype", "309343006", "999"),
        ("date", "2023-01-16", "2024-06-01"),
    ):
        assert medication_request not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert medication_request in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param
    assert medication_request in _ids(
        (await client.get(BASE + "/", params={"code": "9999"})).json()
    )
    assert medication_request in _ids(
        (await client.get(BASE + "/", params={"medication:missing": "true"})).json()
    )


async def test_patch_subject_replaced_and_reindexed(client, patient):
    medication_request = await create_medication_request(
        client, medication_request_body(patient)
    )
    other = await create_patient(client)
    resp = await client.patch(
        f"{BASE}/{medication_request}",
        json={"subject": {"reference": f"Patient/{other}"}},
    )
    assert resp.status_code == 200, resp.text
    assert medication_request not in _ids(
        (await client.get(BASE + "/", params={"patient": str(patient)})).json()
    )
    assert medication_request in _ids(
        (await client.get(BASE + "/", params={"patient": str(other)})).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client, patient):
    medication_request, _ = await _full(client, patient)
    assert medication_request in _ids(
        (await client.get(BASE + "/", params={"identifier": "RX-1001"})).json()
    )
    resp = await client.patch(
        f"{BASE}/{medication_request}",
        json={"identifier": [], "category": [], "dosageInstruction": [], "note": []},
    )
    for gone in ("identifier", "category", "dosageInstruction", "note"):
        assert gone not in resp.json()
    assert resp.json()["status"] == "active"  # untouched
    for param in ("identifier", "category", "date"):
        assert medication_request in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_requester_and_missing_follows(client, patient):
    practitioner = await create_practitioner(client)
    medication_request = await create_medication_request(
        client,
        medication_request_body(
            patient, requester={"reference": f"Practitioner/{practitioner}"}
        ),
    )
    resp = await client.patch(f"{BASE}/{medication_request}", json={"requester": None})
    assert "requester" not in resp.json()
    assert medication_request in _ids(
        (await client.get(BASE + "/", params={"requester:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(
    client, patient
):
    medication_request = await create_medication_request(
        client, medication_request_body(patient)
    )
    resp = await client.patch(
        f"{BASE}/{medication_request}",
        json={"priorPrescription": {"reference": "MedicationRequest/999999"}},
    )
    assert resp.status_code == 422
    assert (
        "priorPrescription"
        not in (await client.get(f"{BASE}/{medication_request}")).json()
    )


async def test_patch_invalid_value_rejected_and_nothing_written(client, patient):
    medication_request = await create_medication_request(
        client, medication_request_body(patient, status="active")
    )
    assert (
        await client.patch(f"{BASE}/{medication_request}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{medication_request}")).json()[
        "status"
    ] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "active"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client, patient):
    medication_request, _ = await _full(client, patient)
    assert (await client.delete(f"{BASE}/{medication_request}")).status_code == 204
    assert (await client.get(f"{BASE}/{medication_request}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "RX-1001"),
        ("category", "outpatient"),
        ("date", "2023-01-16"),
        ("intended-performertype", "309343006"),
    ):
        assert medication_request not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client, patient):
    _as_user(permissions=["medication_request:read"])
    assert (
        await client.post(BASE + "/", json=medication_request_body(patient))
    ).status_code == 403


async def test_org_less_token_rejected(client, patient):
    medication_request = await create_medication_request(
        client, medication_request_body(patient)
    )

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": MEDICATION_REQUEST_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (
        await client.post(BASE + "/", json=medication_request_body())
    ).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{medication_request}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    medication_request = await create_medication_request(
        client, medication_request_body()
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{medication_request}"),
            await other_client.patch(
                f"{BASE}/{medication_request}", json={"status": "active"}
            ),
            await other_client.delete(f"{BASE}/{medication_request}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_medication_request(
        client,
        medication_request_body(
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

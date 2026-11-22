"""Core service request endpoint coverage.

ServiceRequest is stored Medplum-style (like Patient, Encounter, Condition, Procedure,
DiagnosticReport, Observation, Specimen and the other content-based resources): the request body
(genuine FHIR R4 ServiceRequest JSON) is validated and stored whole in `content`, every response
is FHIR R4 (`application/fhir+json`, regardless of Accept), and only the FHIR R4 search
parameters are indexed (https://www.hl7.org/fhir/R4/servicerequest.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`subject`, `encounter`,
`requester`, `performer`, `basedOn`, `replaces`, `specimen`, `locationReference`,
`reasonReference`, `supportingInfo`, note authors and every identifier's `assigner`). Search
lives in test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.service_request.conftest import SERVICE_REQUEST_PERMS
from tests.integration.service_request.support import (
    BASE,
    LOINC,
    SCT,
    concept,
    create_condition,
    create_encounter,
    create_healthcare_service,
    create_location,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_related_person,
    create_service_request,
    create_specimen,
    encounter_body,
    full_body,
    related_person_body,
    service_request_body,
    specimen_body,
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


def _as_user(sub="u-test", org_id="org-test", permissions=SERVICE_REQUEST_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client, patient) -> tuple[int, dict]:
    encounter = await create_encounter(
        client, encounter_body(subject={"reference": f"Patient/{patient}"})
    )
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    location = await create_location(client)
    specimen = await create_specimen(client, specimen_body(patient))
    based_on = await create_service_request(client, service_request_body(patient))
    replaces = await create_service_request(client, service_request_body(patient))
    condition = await create_condition(client, patient)
    body = full_body(
        patient,
        encounter,
        practitioner,
        organization,
        location,
        specimen,
        based_on,
        replaces,
        condition,
    )
    return await create_service_request(client, body), body


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, patient):
    resp = await client.post(BASE + "/", json=service_request_body(patient))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "ServiceRequest"
    assert data["status"] == "active" and data["intent"] == "order"
    assert data["subject"] == {"reference": f"Patient/{patient}"}


async def test_create_full_round_trip(client, patient):
    service_request, body = await _full(client, patient)
    data = (await client.get(f"{BASE}/{service_request}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client, patient):
    """`doNotPerform`, `orderDetail`, `quantity[x]`, `asNeeded[x]`, `locationCode`,
    `locationReference`, `reasonCode`, `reasonReference`, `insurance`, `supportingInfo`, `note`,
    `patientInstruction` and `relevantHistory` live only in `content`."""
    service_request, _ = await _full(client, patient)
    data = (await client.get(f"{BASE}/{service_request}")).json()
    assert data["doNotPerform"] is False
    assert data["orderDetail"][0]["coding"][0]["code"] == "1"
    assert data["quantityQuantity"]["value"] == 2
    assert data["asNeededBoolean"] is True
    assert data["locationCode"][0]["coding"][0]["display"] == "Loc"
    assert data["insurance"] == [{"reference": "Coverage/240001"}]
    assert data["relevantHistory"] == [{"reference": "Provenance/270001"}]
    assert data["patientInstruction"] == "Drink water."
    assert data["note"][0]["authorString"] == "Nurse Joy"
    assert data["reasonCode"][0]["coding"][0]["code"] == "271737000"


@pytest.mark.parametrize(
    "extra",
    [
        {"quantityQuantity": {"value": 2, "unit": "mL"}},
        {
            "quantityRatio": {
                "numerator": {"value": 1, "unit": "mg"},
                "denominator": {"value": 1, "unit": "mL"},
            }
        },
        {"quantityRange": {"low": {"value": 1}, "high": {"value": 3}}},
    ],
    ids=["quantity", "ratio", "range"],
)
async def test_create_each_quantity_choice_round_trips(client, patient, extra):
    resp = await client.post(BASE + "/", json=service_request_body(patient, **extra))
    assert resp.status_code == 201, resp.text
    for key, value in extra.items():
        assert resp.json()[key] == value


@pytest.mark.parametrize(
    "extra",
    [
        {"occurrenceDateTime": "2023-01"},
        {"occurrencePeriod": {"start": "2023-01-01", "end": "2023-01-02"}},
        {"occurrenceTiming": {"event": ["2023-01-01T08:00:00Z"]}},
    ],
    ids=["dateTime", "period", "timing"],
)
async def test_create_each_occurrence_choice_round_trips(client, patient, extra):
    resp = await client.post(BASE + "/", json=service_request_body(patient, **extra))
    assert resp.status_code == 201, resp.text
    for key, value in extra.items():
        assert resp.json()[key] == value


@pytest.mark.parametrize(
    "extra",
    [{"asNeededBoolean": False}, {"asNeededCodeableConcept": {"text": "pain"}}],
    ids=["boolean", "codeableConcept"],
)
async def test_create_each_as_needed_choice_round_trips(client, patient, extra):
    resp = await client.post(BASE + "/", json=service_request_body(patient, **extra))
    assert resp.status_code == 201, resp.text
    for key, value in extra.items():
        assert resp.json()[key] == value


@pytest.mark.parametrize(
    "status",
    [
        "draft",
        "active",
        "on-hold",
        "revoked",
        "completed",
        "entered-in-error",
        "unknown",
    ],
)
async def test_create_every_status_round_trips(client, patient, status):
    resp = await client.post(
        BASE + "/", json=service_request_body(patient, status=status)
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


@pytest.mark.parametrize(
    "intent",
    [
        "proposal",
        "plan",
        "directive",
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
        BASE + "/", json=service_request_body(patient, intent=intent)
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["intent"] == intent


@pytest.mark.parametrize("priority", ["routine", "urgent", "asap", "stat"])
async def test_create_every_priority_round_trips(client, patient, priority):
    resp = await client.post(
        BASE + "/", json=service_request_body(patient, priority=priority)
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["priority"] == priority


async def test_create_ignores_server_managed_id_and_meta(client, patient):
    body = service_request_body(
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
        {"occurrenceDateTime": "noon"},
        {"category": concept(SCT, "1")},
        {"code": "x"},
        {"identifier": {"value": "x"}},
        {"requisition": [{"value": "x"}]},
        {"basedOn": {"reference": "ServiceRequest/1"}},
        {"performer": {"reference": "Organization/1"}},
        {"specimen": {"reference": "Specimen/1"}},
        {"note": {"text": "x"}},
        {"instantiatesUri": "http://x"},
        {"instantiatesCanonical": "http://x"},
        {"doNotPerform": "yes"},
        {"quantityQuantity": "5"},
        {"requester": "Practitioner/1"},
        {"patientInstruction": 5},
    ):
        resp = await client.post(BASE + "/", json=service_request_body(patient, **bad))
        assert resp.status_code == 422, (bad, resp.text)
    resp = await client.post(
        BASE + "/", json={"status": "active", "intent": "order", "subject": "Patient/1"}
    )
    assert resp.status_code == 422


async def test_create_order_detail_without_code_rejected(client, patient):
    """Rule prr-1: `orderDetail` only with a `code` (enforced by the base-R4 validator)."""
    if settings.fhir_validation.backend != "java_validator":
        pytest.skip(
            "rule prr-1 is an invariant: only the java_validator backend enforces it"
        )
    resp = await client.post(
        BASE + "/", json=service_request_body(patient, orderDetail=[{"text": "x"}])
    )
    assert resp.status_code == 422


async def test_create_non_fhir_key_rejected(client, patient, native_validation):
    resp = await client.post(
        BASE + "/", json=service_request_body(patient, not_a_fhir_element=1)
    )
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, patient, native_validation):
    for stale in (
        {"code_text": "x"},
        {"occurrence_date_time": "2020-01-01"},
        {"org_id": "x"},
    ):
        resp = await client.post(
            BASE + "/", json={**service_request_body(patient), **stale}
        )
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, patient):
    resp = await client.post(
        BASE + "/", json=service_request_body(patient, resourceType="Patient")
    )
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client, patient):
    data = (await client.post(BASE + "/", json=service_request_body(patient))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


async def test_create_patient_subject_must_exist(client):
    assert (
        await client.post(BASE + "/", json=service_request_body(999999))
    ).status_code == 422


async def test_create_subject_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert (
        await client.post(BASE + "/", json=service_request_body(theirs))
    ).status_code == 422


async def test_create_subject_is_checked_for_a_patient_or_location_only(client):
    location = await create_location(client)
    ok = service_request_body(subject={"reference": f"Location/{location}"})
    ok["subject"] = {"reference": f"Location/{location}"}
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = {**ok, "subject": {"reference": "Location/999999"}}
    assert (await client.post(BASE + "/", json=missing)).status_code == 422
    # a Group is checked (Group/430001 is seeded); a Device is not rebuilt: stored as sent
    group_missing = {**ok, "subject": {"reference": "Group/999999"}}
    assert (await client.post(BASE + "/", json=group_missing)).status_code == 422
    for stored in ("Group/430001", "Device/999999"):
        body = {**ok, "subject": {"reference": stored}}
        resp = await client.post(BASE + "/", json=body)
        assert resp.status_code == 201, (stored, resp.text)
        assert resp.json()["subject"] == {"reference": stored}


async def test_create_encounter_must_exist(client, patient):
    encounter = await create_encounter(
        client, encounter_body(subject={"reference": f"Patient/{patient}"})
    )
    ok = service_request_body(
        patient, encounter={"reference": f"Encounter/{encounter}"}
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = service_request_body(patient, encounter={"reference": "Encounter/999999"})
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_requester_and_performer_must_exist(client, patient):
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(client)
    organization = await create_organization(client)
    related = await create_related_person(client, related_person_body(patient))
    service = await create_healthcare_service(client)
    for ref in (
        f"Practitioner/{practitioner}",
        f"PractitionerRole/{role}",
        f"Organization/{organization}",
        f"Patient/{patient}",
        f"RelatedPerson/{related}",
    ):
        body = service_request_body(patient, requester={"reference": ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for ref in (
        f"Practitioner/{practitioner}",
        f"PractitionerRole/{role}",
        f"Organization/{organization}",
        f"HealthcareService/{service}",
        f"Patient/{patient}",
        f"RelatedPerson/{related}",
    ):
        body = service_request_body(patient, performer=[{"reference": ref}])
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for missing in (
        "Practitioner/999999",
        "Organization/999999",
        "RelatedPerson/999999",
    ):
        body = service_request_body(patient, requester={"reference": missing})
        assert (await client.post(BASE + "/", json=body)).status_code == 422, missing
        body = service_request_body(patient, performer=[{"reference": missing}])
        assert (await client.post(BASE + "/", json=body)).status_code == 422, missing
    body = service_request_body(
        patient, performer=[{"reference": "HealthcareService/999999"}]
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_unmodeled_requesters_and_performers_not_checked(client, patient):
    body = service_request_body(
        patient,
        requester={"reference": "Device/999999"},
        performer=[
            {"reference": "Device/999999"},
        ],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_based_on_and_replaces_must_exist(client, patient):
    first = await create_service_request(client, service_request_body(patient))
    ok = service_request_body(
        patient,
        basedOn=[{"reference": f"ServiceRequest/{first}"}],
        replaces=[{"reference": f"ServiceRequest/{first}"}],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for element in ("basedOn", "replaces"):
        body = service_request_body(
            patient, **{element: [{"reference": "ServiceRequest/999999"}]}
        )
        assert (await client.post(BASE + "/", json=body)).status_code == 422, element


async def test_create_based_on_care_plan_must_exist(client, patient):
    from tests.helpers.care_plans import create_minimal_care_plan

    plan = await create_minimal_care_plan(client)
    ok = service_request_body(patient, basedOn=[{"reference": f"CarePlan/{plan}"}])
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = service_request_body(patient, basedOn=[{"reference": "CarePlan/999999"}])
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_specimen_must_exist(client, patient):
    specimen = await create_specimen(client, specimen_body(patient))
    ok = service_request_body(patient, specimen=[{"reference": f"Specimen/{specimen}"}])
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = service_request_body(patient, specimen=[{"reference": "Specimen/999999"}])
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_location_reference_must_exist(client, patient):
    location = await create_location(client)
    ok = service_request_body(
        patient, locationReference=[{"reference": f"Location/{location}"}]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = service_request_body(
        patient, locationReference=[{"reference": "Location/999999"}]
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_reason_reference_is_checked_for_rebuilt_types(client, patient):
    condition = await create_condition(client, patient)
    ok = service_request_body(
        patient, reasonReference=[{"reference": f"Condition/{condition}"}]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for missing in (
        "Condition/999999",
        "Observation/999999",
        "DiagnosticReport/999999",
    ):
        body = service_request_body(patient, reasonReference=[{"reference": missing}])
        assert (await client.post(BASE + "/", json=body)).status_code == 422, missing
    stored = service_request_body(
        patient, reasonReference=[{"reference": "DocumentReference/999999"}]
    )
    assert (await client.post(BASE + "/", json=stored)).status_code == 201


async def test_create_supporting_info_is_checked_for_rebuilt_types(client, patient):
    ok = service_request_body(
        patient, supportingInfo=[{"reference": f"Patient/{patient}"}]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = service_request_body(
        patient, supportingInfo=[{"reference": "Observation/999999"}]
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422
    stored = service_request_body(
        patient, supportingInfo=[{"reference": "DocumentReference/999999"}]
    )
    assert (await client.post(BASE + "/", json=stored)).status_code == 201


async def test_create_insurance_and_history_are_not_checked(client, patient):
    body = service_request_body(
        patient,
        insurance=[
            {"reference": "Coverage/999999"},
            {"reference": "ClaimResponse/999999"},
        ],
        relevantHistory=[{"reference": "Provenance/999999"}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_note_author_is_checked(client, patient):
    practitioner = await create_practitioner(client)
    ok = service_request_body(
        patient,
        note=[
            {
                "text": "n",
                "authorReference": {"reference": f"Practitioner/{practitioner}"},
            }
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = service_request_body(
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
        ({"requisition": ok}, {"requisition": missing}),
    ):
        assert (
            await client.post(BASE + "/", json=service_request_body(patient, **good))
        ).status_code == 201, good
        assert (
            await client.post(BASE + "/", json=service_request_body(patient, **bad))
        ).status_code == 422, bad


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/1"
    resp = await client.post(BASE + "/", json=service_request_body())
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": absolute}
    logical = {
        "identifier": {"system": "urn:pts", "value": "P-9"},
        "display": "External",
    }
    body = {
        "status": "active",
        "intent": "order",
        "subject": logical,
        "requester": {"reference": "https://other.example.org/fhir/Practitioner/7"},
        "basedOn": [{"identifier": {"system": "urn:orders", "value": "O-1"}}],
    }
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == logical
    assert resp.json()["basedOn"] == body["basedOn"]


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, patient):
    service_request, _ = await _full(client, patient)
    resp = await client.get(f"{BASE}/{service_request}")
    assert resp.status_code == 200 and resp.json()["id"] == str(service_request)


async def test_get_is_fhir_regardless_of_accept(client, patient):
    service_request = await create_service_request(
        client, service_request_body(patient)
    )
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{service_request}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "ServiceRequest"


async def test_xml_only_accept_is_406(client, patient):
    service_request = await create_service_request(
        client, service_request_body(patient)
    )
    resp = await client.get(
        f"{BASE}/{service_request}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, patient):
    service_request, _ = await _full(client, patient)
    resp = await client.patch(
        f"{BASE}/{service_request}",
        json={"status": "completed", "priority": "stat", "note": [{"text": "Done"}]},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "completed" and resp.json()["priority"] == "stat"
    assert resp.json()["note"] == [{"text": "Done"}]
    assert resp.json()["subject"] == {"reference": f"Patient/{patient}"}  # untouched
    assert resp.json()["intent"] == "order"
    assert resp.json()["code"]["coding"][0]["code"] == "58410-2"


async def test_patch_reindexes_search(client, patient):
    service_request, _ = await _full(client, patient)
    await client.patch(
        f"{BASE}/{service_request}",
        json={
            "status": "revoked",
            "intent": "plan",
            "priority": "routine",
            "code": concept(LOINC, "9999-9"),
            "authoredOn": "2024-05-01",
            "occurrenceDateTime": "2024-06-01",
            "requisition": {"system": "urn:rq", "value": "NEW-1"},
            "bodySite": [concept(SCT, "999")],
            "category": [concept(SCT, "888")],
        },
    )
    for param, old, new in (
        ("status", "active", "revoked"),
        ("intent", "order", "plan"),
        ("priority", "urgent", "routine"),
        ("code", "58410-2", "9999-9"),
        ("authored", "2023-01-15", "2024-05-01"),
        ("occurrence", "2023-01-16", "2024-06-01"),
        ("requisition", "RQ-1", "NEW-1"),
        ("body-site", "368208006", "999"),
        ("category", "108252007", "888"),
    ):
        assert service_request not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert service_request in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_subject_replaced_and_reindexed(client, patient):
    service_request = await create_service_request(
        client, service_request_body(patient)
    )
    other = await create_patient(client)
    resp = await client.patch(
        f"{BASE}/{service_request}", json={"subject": {"reference": f"Patient/{other}"}}
    )
    assert resp.status_code == 200, resp.text
    assert service_request not in _ids(
        (await client.get(BASE + "/", params={"patient": str(patient)})).json()
    )
    assert service_request in _ids(
        (await client.get(BASE + "/", params={"patient": str(other)})).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client, patient):
    service_request, _ = await _full(client, patient)
    assert service_request in _ids(
        (await client.get(BASE + "/", params={"identifier": "SR-1001"})).json()
    )
    resp = await client.patch(
        f"{BASE}/{service_request}",
        json={
            "identifier": [],
            "basedOn": [],
            "replaces": [],
            "specimen": [],
            "performer": [],
            "category": [],
            "instantiatesUri": [],
            "instantiatesCanonical": [],
            "note": [],
        },
    )
    for gone in ("identifier", "basedOn", "performer", "specimen", "category", "note"):
        assert gone not in resp.json()
    assert resp.json()["status"] == "active"  # untouched
    assert service_request not in _ids(
        (await client.get(BASE + "/", params={"identifier": "SR-1001"})).json()
    )
    for param in (
        "based-on",
        "replaces",
        "specimen",
        "performer",
        "category",
        "instantiates-uri",
        "instantiates-canonical",
    ):
        assert service_request in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_requester_and_missing_follows(client, patient):
    practitioner = await create_practitioner(client)
    service_request = await create_service_request(
        client,
        service_request_body(
            patient, requester={"reference": f"Practitioner/{practitioner}"}
        ),
    )
    resp = await client.patch(f"{BASE}/{service_request}", json={"requester": None})
    assert "requester" not in resp.json()
    assert service_request in _ids(
        (await client.get(BASE + "/", params={"requester:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(
    client, patient
):
    service_request = await create_service_request(
        client, service_request_body(patient)
    )
    resp = await client.patch(
        f"{BASE}/{service_request}",
        json={"specimen": [{"reference": "Specimen/999999"}]},
    )
    assert resp.status_code == 422
    assert "specimen" not in (await client.get(f"{BASE}/{service_request}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client, patient):
    service_request = await create_service_request(
        client, service_request_body(patient, status="active")
    )
    assert (
        await client.patch(f"{BASE}/{service_request}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{service_request}")).json()["status"] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "active"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, patient):
    service_request, _ = await _full(client, patient)
    assert (await client.delete(f"{BASE}/{service_request}")).status_code == 204
    assert (await client.get(f"{BASE}/{service_request}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "SR-1001"),
        ("code", "58410-2"),
        ("requisition", "RQ-1"),
        ("instantiates-uri", "http://example.org/protocols/cbc"),
    ):
        assert service_request not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, patient):
    _as_user(permissions=["service_request:read"])
    assert (
        await client.post(BASE + "/", json=service_request_body(patient))
    ).status_code == 403


async def test_org_less_token_rejected(client, patient):
    service_request = await create_service_request(
        client, service_request_body(patient)
    )

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": SERVICE_REQUEST_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (
        await client.post(BASE + "/", json=service_request_body())
    ).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{service_request}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    service_request = await create_service_request(client, service_request_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{service_request}"),
            await other_client.patch(
                f"{BASE}/{service_request}", json={"status": "active"}
            ),
            await other_client.delete(f"{BASE}/{service_request}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_service_request(
        client,
        service_request_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


async def test_create_based_on_and_supporting_info_medication_request_must_exist(
    client, patient
):
    from tests.helpers.medication_requests import create_minimal_medication_request

    existing = await create_minimal_medication_request(client)
    ref = {"reference": f"MedicationRequest/{existing}"}
    for element in ("basedOn", "supportingInfo"):
        ok = service_request_body(patient, **{element: [ref]})
        assert (await client.post(BASE + "/", json=ok)).status_code == 201, element
        missing = service_request_body(
            patient, **{element: [{"reference": "MedicationRequest/999999"}]}
        )
        assert (await client.post(BASE + "/", json=missing)).status_code == 422, element

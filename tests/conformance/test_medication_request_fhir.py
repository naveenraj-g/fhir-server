"""FHIR R4 conformance for `to_fhir_medication_request()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

MedicationRequest is stored Medplum-style (like Patient, Appointment, Encounter, Condition,
Procedure, Specimen, ServiceRequest, Medication and the other content-based resources): the
resource lives whole in MedicationRequestModel.content, and to_fhir_medication_request() only
stamps `id` and `meta` onto it. So what can go wrong on the read side is that stamping (e.g. a
malformed meta extension) or a stored document the server returns that isn't valid R4 - each
case below is a `content` document as the write path would store it, run through the real read
mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.medication_request import to_fhir_medication_request
from app.models.medication_request import MedicationRequestModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.medication_request_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
SCT = "http://snomed.info/sct"
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
BASE = {
    "status": "active",
    "intent": "order",
    "medicationCodeableConcept": {"text": "Aspirin"},
    "subject": {"reference": "Patient/10001"},
}
CODE = {"coding": [{"system": RXNORM, "code": "1049502", "display": "Oxycodone"}]}


def _qty(value, unit="tablet"):
    return {"value": value, "unit": unit}


def _mr(content: dict, **overrides) -> MedicationRequestModel:
    fields = {
        "medication_request_id": 90001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return MedicationRequestModel(**fields)


def _with(**extra) -> MedicationRequestModel:
    return _mr({**BASE, **extra})


CASES = {
    "minimal": _mr(BASE),
    "updated_by_and_updated_at": _mr(BASE, updated_by="u-other", updated_at=D),
    "identifier_with_type_and_assigner": _with(
        identifier=[
            {
                "use": "official",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "PLAC",
                        }
                    ]
                },
                "system": "https://fhir-server.dev/fhir/identifier-system/prescription-id",
                "value": "RX-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    **{
        f"status_{s}": _mr({**BASE, "status": s})
        for s in (
            "active",
            "on-hold",
            "cancelled",
            "completed",
            "entered-in-error",
            "stopped",
            "draft",
            "unknown",
        )
    },
    "status_reason": _with(statusReason={"coding": [{"system": SCT, "code": "1"}]}),
    **{
        f"intent_{i}": _mr({**BASE, "intent": i})
        for i in (
            "proposal",
            "plan",
            "order",
            "original-order",
            "reflex-order",
            "filler-order",
            "instance-order",
            "option",
        )
    },
    "category": _with(category=[{"coding": [{"system": SCT, "code": "1"}]}]),
    **{
        f"priority_{p}": _with(priority=p)
        for p in ("routine", "urgent", "asap", "stat")
    },
    "do_not_perform": _with(doNotPerform=True),
    "reported_boolean": _with(reportedBoolean=True),
    **{
        f"reported_reference_{t}": _with(reportedReference={"reference": f"{t}/1"})
        for t in (
            "Patient",
            "Practitioner",
            "PractitionerRole",
            "RelatedPerson",
            "Organization",
        )
    },
    "medication_codeable_concept": _mr({**BASE, "medicationCodeableConcept": CODE}),
    "medication_reference": _mr(
        {
            "status": "active",
            "intent": "order",
            "medicationReference": {
                "reference": "Medication/250001",
                "display": "Aspirin",
            },
            "subject": {"reference": "Patient/10001"},
        }
    ),
    **{
        f"subject_{t}": _mr({**BASE, "subject": {"reference": f"{t}/1"}})
        for t in ("Patient", "Group")
    },
    "subject_logical": _mr(
        {**BASE, "subject": {"identifier": {"system": "urn:pts", "value": "P-9"}}}
    ),
    "subject_absolute_url": _mr(
        {**BASE, "subject": {"reference": "https://other.example.org/fhir/Patient/9"}}
    ),
    "encounter": _with(encounter={"reference": "Encounter/20001"}),
    "supporting_information": _with(
        supportingInformation=[
            {"reference": "Observation/160001"},
            {"reference": "Patient/1"},
        ]
    ),
    "authored_on": _with(authoredOn="2023-01-15T09:30:00Z"),
    "authored_on_partial": _with(authoredOn="2023"),
    **{
        f"requester_{t}": _with(requester={"reference": f"{t}/1"})
        for t in (
            "Practitioner",
            "PractitionerRole",
            "Organization",
            "Patient",
            "RelatedPerson",
            "Device",
        )
    },
    **{
        f"performer_{t}": _with(performer={"reference": f"{t}/1"})
        for t in (
            "Practitioner",
            "PractitionerRole",
            "Organization",
            "Patient",
            "Device",
            "RelatedPerson",
            "CareTeam",
        )
    },
    "performer_type": _with(
        performerType={"coding": [{"system": SCT, "code": "309343006"}]}
    ),
    "recorder": _with(recorder={"reference": "Practitioner/30001"}),
    "reason": _with(
        reasonCode=[{"coding": [{"system": SCT, "code": "22253000"}]}],
        reasonReference=[
            {"reference": "Condition/120001"},
            {"reference": "Observation/160001"},
        ],
    ),
    "instantiates": _with(
        instantiatesCanonical=["http://example.org/fhir/PlanDefinition/pain|1.0"],
        instantiatesUri=["http://example.org/protocols/pain"],
    ),
    "based_on": _with(
        basedOn=[
            {"reference": "MedicationRequest/90000"},
            {"reference": "ServiceRequest/80001"},
            {"reference": "CarePlan/290001"},
            {"reference": "ImmunizationRecommendation/510001"},
        ]
    ),
    "group_identifier": _with(groupIdentifier={"system": "urn:grp", "value": "G-1"}),
    "course_of_therapy_type": _with(
        courseOfTherapyType={"coding": [{"system": SCT, "code": "1"}]}
    ),
    "insurance": _with(
        insurance=[
            {"reference": "Coverage/240001"},
            {"reference": "ClaimResponse/180001"},
        ]
    ),
    "note_author_string": _with(
        note=[
            {
                "text": "Fasting.",
                "time": "2023-01-15T10:00:00Z",
                "authorString": "Nurse Joy",
            }
        ]
    ),
    "note_author_reference": _with(
        note=[{"text": "n", "authorReference": {"reference": "Practitioner/30001"}}]
    ),
    "dosage_instruction": _with(
        dosageInstruction=[
            {
                "sequence": 1,
                "text": "1 tablet every 12 hours",
                "additionalInstruction": [{"text": "with food"}],
                "patientInstruction": "Take with food",
                "timing": {
                    "event": ["2023-01-16T08:00:00Z"],
                    "repeat": {"frequency": 1, "period": 12, "periodUnit": "h"},
                },
                "asNeededBoolean": False,
                "site": {"text": "mouth"},
                "route": {"coding": [{"system": SCT, "code": "26643006"}]},
                "method": {"text": "swallow"},
                "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}],
                "maxDosePerPeriod": {
                    "numerator": {"value": 2, "unit": "tablet"},
                    "denominator": {"value": 1, "unit": "d"},
                },
                "maxDosePerAdministration": {"value": 1, "unit": "tablet"},
                "maxDosePerLifetime": {"value": 100, "unit": "tablet"},
            },
            {"asNeededCodeableConcept": {"text": "pain"}},
        ]
    ),
    "dispense_request": _with(
        dispenseRequest={
            "initialFill": {
                "quantity": _qty(30),
                "duration": {"value": 7, "unit": "days"},
            },
            "dispenseInterval": {"value": 7, "unit": "days"},
            "validityPeriod": {"start": "2023-01-15", "end": "2023-07-15"},
            "numberOfRepeatsAllowed": 2,
            "quantity": _qty(60),
            "expectedSupplyDuration": {"value": 30, "unit": "days"},
            "performer": {"reference": "Organization/190001"},
        }
    ),
    "substitution_boolean": _with(substitution={"allowedBoolean": True}),
    "substitution_codeable_concept": _with(
        substitution={
            "allowedCodeableConcept": {"text": "generic"},
            "reason": {"text": "cost"},
        }
    ),
    "prior_prescription": _with(
        priorPrescription={"reference": "MedicationRequest/90000"}
    ),
    "detected_issue": _with(detectedIssue=[{"reference": "DetectedIssue/540001"}]),
    "event_history": _with(eventHistory=[{"reference": "Provenance/270001"}]),
    "extension": _with(
        extension=[
            {
                "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                "valueString": "y",
            }
        ]
    ),
    "full": _with(
        identifier=[{"system": "urn:rx", "value": "RX-1"}],
        category=[{"text": "Outpatient"}],
        priority="urgent",
        encounter={"reference": "Encounter/20001"},
        authoredOn="2023-01-15T09:30:00Z",
        requester={"reference": "Practitioner/30001"},
        performer={"reference": "Organization/190001"},
        reasonCode=[{"text": "Pain"}],
        basedOn=[{"reference": "MedicationRequest/90000"}],
        note=[{"text": "n"}],
        dosageInstruction=[{"text": "1 tablet"}],
        dispenseRequest={"quantity": _qty(60)},
        substitution={"allowedBoolean": False},
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_medication_request_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.MedicationRequest, to_fhir_medication_request(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {**BASE, "priority": "stat", "authoredOn": "2023-01-15"}
    out = to_fhir_medication_request(_mr(content))
    assert out["resourceType"] == "MedicationRequest"
    assert out["id"] == "90001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `subject`, `requester` or `dispenseRequest` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("subject as string not a Reference", {"subject": "Patient/1"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("intent with an unknown code", {"intent": "robot"}),
        ("priority with an unknown code", {"priority": "robot"}),
        ("authoredOn not a dateTime", {"authoredOn": "yesterday"}),
        ("category as object not a list", {"category": {"text": "x"}}),
        ("medicationCodeableConcept as string", {"medicationCodeableConcept": "x"}),
        ("medicationReference as string", {"medicationReference": "Medication/1"}),
        ("doNotPerform as string", {"doNotPerform": "yes"}),
        ("reportedBoolean as string", {"reportedBoolean": "yes"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("groupIdentifier as string", {"groupIdentifier": "G-1"}),
        ("encounter as string", {"encounter": "Encounter/1"}),
        ("requester as string", {"requester": "Practitioner/1"}),
        ("performer as list", {"performer": [{"reference": "Organization/1"}]}),
        ("performerType as string", {"performerType": "x"}),
        ("recorder as string", {"recorder": "Practitioner/1"}),
        (
            "reasonReference as object",
            {"reasonReference": {"reference": "Condition/1"}},
        ),
        (
            "basedOn as object not a list",
            {"basedOn": {"reference": "MedicationRequest/1"}},
        ),
        ("note as object not a list", {"note": {"text": "x"}}),
        ("instantiatesUri as string", {"instantiatesUri": "http://x"}),
        (
            "dosageInstruction as object not a list",
            {"dosageInstruction": {"text": "x"}},
        ),
        ("dosage sequence as string", {"dosageInstruction": [{"sequence": "one"}]}),
        ("dosage text as number", {"dosageInstruction": [{"text": 5}]}),
        ("dispenseRequest as string", {"dispenseRequest": "x"}),
        ("dispenseRequest quantity as string", {"dispenseRequest": {"quantity": "60"}}),
        (
            "dispenseRequest numberOfRepeatsAllowed negative",
            {"dispenseRequest": {"numberOfRepeatsAllowed": -1}},
        ),
        (
            "dispenseRequest performer as string",
            {"dispenseRequest": {"performer": "Organization/1"}},
        ),
        ("substitution as string", {"substitution": "x"}),
        (
            "substitution allowedBoolean as string",
            {"substitution": {"allowedBoolean": "yes"}},
        ),
        (
            "priorPrescription as list",
            {"priorPrescription": [{"reference": "MedicationRequest/1"}]},
        ),
        (
            "detectedIssue as object",
            {"detectedIssue": {"reference": "DetectedIssue/1"}},
        ),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "MedicationRequest", "id": "90001", **BASE, **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.MedicationRequest, validate=True
        )

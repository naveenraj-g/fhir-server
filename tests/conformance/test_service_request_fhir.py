"""FHIR R4 conformance for `to_fhir_service_request()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

ServiceRequest is stored Medplum-style (like Patient, Appointment, Encounter, Condition,
Procedure, DiagnosticReport, Observation, Specimen and the other content-based resources): the
resource lives whole in ServiceRequestModel.content, and to_fhir_service_request() only stamps
`id` and `meta` onto it. So what can go wrong on the read side is that stamping (e.g. a malformed
meta extension) or a stored document the server returns that isn't valid R4 — each case below is a
`content` document as the write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.service_request import to_fhir_service_request
from app.models.service_request import ServiceRequestModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.service_request_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
SCT = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"
BASE = {
    "status": "active",
    "intent": "order",
    "subject": {"reference": "Patient/10001"},
}
CODE = {
    "coding": [
        {"system": "http://loinc.org", "code": "58410-2", "display": "CBC panel"}
    ]
}


def _qty(value, unit="mL", code="mL"):
    return {"value": value, "unit": unit, "system": UCUM, "code": code}


def _sr(content: dict, **overrides) -> ServiceRequestModel:
    fields = {
        "service_request_id": 80001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return ServiceRequestModel(**fields)


def _with(**extra) -> ServiceRequestModel:
    return _sr({**BASE, **extra})


CASES = {
    "minimal": _sr(BASE),
    "updated_by_and_updated_at": _sr(BASE, updated_by="u-other", updated_at=D),
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
                "system": "https://fhir-server.dev/fhir/identifier-system/service-request-id",
                "value": "SR-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "instantiates": _with(
        instantiatesCanonical=[
            "http://example.org/fhir/PlanDefinition/cbc|1.0",
            "http://example.org/fhir/ActivityDefinition/draw",
        ],
        instantiatesUri=["http://example.org/protocols/cbc"],
    ),
    "based_on": _with(
        basedOn=[
            {"reference": "ServiceRequest/80000"},
            {"reference": "CarePlan/290001"},
            {"reference": "MedicationRequest/90001"},
        ]
    ),
    "replaces": _with(replaces=[{"reference": "ServiceRequest/80000"}]),
    "requisition": _with(
        requisition={"system": "http://lab.example.org/requisitions", "value": "RQ-1"}
    ),
    **{
        f"status_{s}": _sr({**BASE, "status": s})
        for s in (
            "draft",
            "active",
            "on-hold",
            "revoked",
            "completed",
            "entered-in-error",
            "unknown",
        )
    },
    **{
        f"intent_{i}": _sr({**BASE, "intent": i})
        for i in (
            "proposal",
            "plan",
            "directive",
            "order",
            "original-order",
            "reflex-order",
            "filler-order",
            "instance-order",
            "option",
        )
    },
    **{
        f"priority_{p}": _with(priority=p)
        for p in ("routine", "urgent", "asap", "stat")
    },
    "category": _with(category=[{"coding": [{"system": SCT, "code": "108252007"}]}]),
    "do_not_perform": _with(doNotPerform=True),
    "code": _with(code=CODE),
    "order_detail": _with(code=CODE, orderDetail=[{"text": "left arm"}]),
    "quantity_quantity": _with(quantityQuantity=_qty(2)),
    "quantity_quantity_comparator": _with(
        quantityQuantity={**_qty(2), "comparator": ">="}
    ),
    "quantity_ratio": _with(
        quantityRatio={"numerator": _qty(1, "mg", "mg"), "denominator": _qty(1)}
    ),
    "quantity_range": _with(quantityRange={"low": _qty(1), "high": _qty(3)}),
    **{
        f"subject_{t}": _sr({**BASE, "subject": {"reference": f"{t}/1"}})
        for t in ("Patient", "Group", "Location", "Device")
    },
    "subject_with_display": _sr(
        {**BASE, "subject": {"reference": "Patient/10001", "display": "A. Patient"}}
    ),
    "subject_logical": _sr(
        {**BASE, "subject": {"identifier": {"system": "urn:pts", "value": "P-9"}}}
    ),
    "subject_absolute_url": _sr(
        {**BASE, "subject": {"reference": "https://other.example.org/fhir/Patient/9"}}
    ),
    "encounter": _with(encounter={"reference": "Encounter/20001"}),
    "occurrence_date_time": _with(occurrenceDateTime="2023-01-16T09:00:00Z"),
    "occurrence_date_time_partial": _with(occurrenceDateTime="2023-01"),
    "occurrence_period": _with(
        occurrencePeriod={"start": "2023-01-01", "end": "2023-01-02"}
    ),
    "occurrence_timing": _with(
        occurrenceTiming={
            "event": ["2023-01-01T08:00:00Z"],
            "repeat": {"frequency": 1, "period": 1, "periodUnit": "d"},
        }
    ),
    "as_needed_boolean": _with(asNeededBoolean=True),
    "as_needed_codeable_concept": _with(
        asNeededCodeableConcept={"coding": [{"system": SCT, "code": "225368008"}]}
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
    "performer_type": _with(
        performerType={"coding": [{"system": SCT, "code": "309343006"}]}
    ),
    "performer": _with(
        performer=[
            {"reference": f"{t}/1"}
            for t in (
                "Practitioner",
                "PractitionerRole",
                "Organization",
                "CareTeam",
                "HealthcareService",
                "Patient",
                "Device",
                "RelatedPerson",
            )
        ]
    ),
    "location": _with(
        locationCode=[{"coding": [{"system": SCT, "code": "1"}]}],
        locationReference=[{"reference": "Location/230001"}],
    ),
    "reason": _with(
        reasonCode=[{"coding": [{"system": SCT, "code": "271737000"}]}],
        reasonReference=[
            {"reference": f"{t}/1"}
            for t in (
                "Condition",
                "Observation",
                "DiagnosticReport",
                "DocumentReference",
            )
        ],
    ),
    "insurance": _with(
        insurance=[
            {"reference": "Coverage/240001"},
            {"reference": "ClaimResponse/180001"},
        ]
    ),
    "supporting_info": _with(
        supportingInfo=[{"reference": "Observation/160001"}, {"reference": "Patient/1"}]
    ),
    "specimen": _with(specimen=[{"reference": "Specimen/310001"}]),
    "body_site": _with(
        bodySite=[{"coding": [{"system": SCT, "code": "368208006"}], "text": "arm"}]
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
    "patient_instruction": _with(patientInstruction="Drink water."),
    "relevant_history": _with(relevantHistory=[{"reference": "Provenance/270001"}]),
    "extension": _with(
        extension=[
            {
                "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                "valueString": "y",
            }
        ]
    ),
    "full": _with(
        identifier=[{"system": "urn:sr", "value": "SR-1"}],
        instantiatesUri=["http://example.org/protocols/cbc"],
        basedOn=[{"reference": "ServiceRequest/80000"}],
        requisition={"system": "urn:rq", "value": "RQ-1"},
        category=[{"text": "Lab"}],
        priority="urgent",
        code=CODE,
        quantityQuantity=_qty(2),
        encounter={"reference": "Encounter/20001"},
        occurrenceDateTime="2023-01-16T09:00:00Z",
        authoredOn="2023-01-15T09:30:00Z",
        requester={"reference": "Practitioner/30001"},
        performer=[{"reference": "Organization/190001"}],
        reasonCode=[{"text": "Anemia"}],
        specimen=[{"reference": "Specimen/310001"}],
        bodySite=[{"text": "arm"}],
        note=[{"text": "n"}],
        patientInstruction="Drink water.",
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_service_request_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.ServiceRequest, to_fhir_service_request(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {**BASE, "priority": "stat", "occurrenceDateTime": "2023-01-15"}
    out = to_fhir_service_request(_sr(content))
    assert out["resourceType"] == "ServiceRequest"
    assert out["id"] == "80001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — `code`, `subject` or `requester` as a one-item list; the
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
        ("code as string not a CodeableConcept", {"code": "x"}),
        ("category as object not a list", {"category": {"text": "x"}}),
        ("authoredOn not a dateTime", {"authoredOn": "yesterday"}),
        ("occurrenceDateTime not a dateTime", {"occurrenceDateTime": "noon"}),
        ("occurrencePeriod as string", {"occurrencePeriod": "2023"}),
        ("doNotPerform as string", {"doNotPerform": "yes"}),
        ("quantityQuantity as string", {"quantityQuantity": "5"}),
        ("asNeededBoolean as string", {"asNeededBoolean": "yes"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("requisition as string", {"requisition": "RQ-1"}),
        (
            "basedOn as object not a list",
            {"basedOn": {"reference": "ServiceRequest/1"}},
        ),
        (
            "replaces as object not a list",
            {"replaces": {"reference": "ServiceRequest/1"}},
        ),
        ("encounter as string", {"encounter": "Encounter/1"}),
        ("requester as string", {"requester": "Practitioner/1"}),
        ("performerType as string", {"performerType": "x"}),
        (
            "performer as object not a list",
            {"performer": {"reference": "Organization/1"}},
        ),
        (
            "locationReference as object",
            {"locationReference": {"reference": "Location/1"}},
        ),
        (
            "reasonReference as object",
            {"reasonReference": {"reference": "Condition/1"}},
        ),
        ("specimen as object not a list", {"specimen": {"reference": "Specimen/1"}}),
        ("bodySite as object not a list", {"bodySite": {"text": "x"}}),
        ("note as object not a list", {"note": {"text": "x"}}),
        ("instantiatesUri as string", {"instantiatesUri": "http://x"}),
        ("instantiatesCanonical as string", {"instantiatesCanonical": "http://x"}),
        ("patientInstruction as number", {"patientInstruction": 5}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "ServiceRequest", "id": "80001", **BASE, **broken}
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.ServiceRequest, validate=True
        )

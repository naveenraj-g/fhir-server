"""FHIR R4 conformance for `to_fhir_medication_administration()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

MedicationAdministration is stored whole in `content` (like MedicationStatement, MedicationRequest
and the other content-based resources): the resource lives in
MedicationAdministrationModel.content, and to_fhir_medication_administration() only stamps `id`
and `meta` onto it. So what can go wrong on the read side is that stamping (e.g. a malformed meta
extension) or a stored document the server returns that isn't valid R4 - each case below is a
`content` document as the write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.medication_administration import (
    to_fhir_medication_administration,
)
from app.models.medication_administration import MedicationAdministrationModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.medication_administration_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
SCT = "http://snomed.info/sct"
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
UCUM = "http://unitsofmeasure.org"


def _c(content: dict, **overrides) -> MedicationAdministrationModel:
    fields = {
        "medication_administration_id": 580001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return MedicationAdministrationModel(**fields)


def _base(**extra) -> dict:
    return {
        "status": "completed",
        "medicationCodeableConcept": {"text": "Aspirin"},
        "subject": {"reference": "Patient/10001"},
        "effectiveDateTime": "2026-02-03T08:30:00Z",
        **extra,
    }


CASES = {
    "minimal": _c(_base()),
    "updated_by_and_updated_at": _c(_base(), updated_by="u-other", updated_at=D),
    **{
        f"status_{s}": _c(_base(status=s))
        for s in (
            "in-progress",
            "not-done",
            "on-hold",
            "completed",
            "entered-in-error",
            "stopped",
            "unknown",
        )
    },
    "identifier": _c(
        _base(
            identifier=[
                {
                    "use": "official",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "ADM",
                            }
                        ]
                    },
                    "system": "https://fhir-server.dev/fhir/identifier-system/medication-administration-id",
                    "value": "MA-1",
                    "period": {"start": "2020-01-01"},
                    "assigner": {"reference": "Organization/190001"},
                },
                {"system": "urn:other", "value": "second"},
            ]
        )
    ),
    "instantiates_and_part_of": _c(
        _base(
            instantiates=["http://example.org/protocol/1", "urn:uuid:1234"],
            partOf=[
                {"reference": "Procedure/100001"},
                {"reference": "MedicationAdministration/580002"},
            ],
        )
    ),
    "status_reason_and_category": _c(
        _base(
            status="not-done",
            statusReason=[
                {
                    "coding": [{"system": SCT, "code": "182856006"}],
                    "text": "Unavailable",
                }
            ],
            category={
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/medication-admin-category",
                        "code": "inpatient",
                    }
                ]
            },
        )
    ),
    "medication_coded": _c(
        _base(
            medicationCodeableConcept={
                "coding": [
                    {"system": RXNORM, "code": "197361", "display": "Amlodipine"}
                ]
            }
        )
    ),
    "medication_reference": _c(
        {
            "status": "completed",
            "medicationReference": {"reference": "Medication/250001"},
            "subject": {"reference": "Patient/10001"},
            "effectivePeriod": {"start": "2026-01-01"},
        }
    ),
    "subject_group": _c(_base(subject={"reference": "Group/430001"})),
    "subject_absolute_url": _c(
        _base(subject={"reference": "https://other.example.org/fhir/Patient/1"})
    ),
    "subject_logical_identifier": _c(
        _base(subject={"identifier": {"system": "urn:mrn", "value": "M-1"}})
    ),
    "context": _c(_base(context={"reference": "Encounter/20001"})),
    "context_episode": _c(_base(context={"reference": "EpisodeOfCare/350001"})),
    "supporting_information": _c(
        _base(
            supportingInformation=[
                {"reference": "Observation/160001"},
                {"reference": "https://other.example.org/fhir/Thing/9"},
            ]
        )
    ),
    "effective_partial_date": _c(_base(effectiveDateTime="2026-02")),
    "effective_period": _c(
        {
            "status": "in-progress",
            "medicationCodeableConcept": {"text": "Aspirin"},
            "subject": {"reference": "Patient/10001"},
            "effectivePeriod": {"start": "2026-01-01", "end": "2026-03-01"},
        }
    ),
    **{
        f"performer_{t}": _c(_base(performer=[{"actor": {"reference": f"{t}/1"}}]))
        for t in (
            "Practitioner",
            "PractitionerRole",
            "Patient",
            "RelatedPerson",
            "Device",
        )
    },
    "performer_with_function": _c(
        _base(
            performer=[
                {
                    "function": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/med-admin-perform-function",
                                "code": "performer",
                            }
                        ]
                    },
                    "actor": {"reference": "Practitioner/30001"},
                }
            ]
        )
    ),
    "reasons": _c(
        _base(
            reasonCode=[
                {
                    "coding": [{"system": SCT, "code": "38341003"}],
                    "text": "Hypertension",
                }
            ],
            reasonReference=[
                {"reference": "Condition/120001"},
                {"reference": "Observation/160001"},
                {"reference": "DiagnosticReport/110001"},
            ],
        )
    ),
    "request_device_event_history": _c(
        _base(
            request={"reference": "MedicationRequest/90001"},
            device=[{"reference": "Device/12"}, {"reference": "Device/13"}],
            eventHistory=[{"reference": "Provenance/270001"}],
        )
    ),
    "note": _c(
        _base(
            note=[
                {
                    "authorReference": {"reference": "Practitioner/30001"},
                    "time": "2026-01-15T10:06:00Z",
                    "text": "Given with water",
                },
                {"authorString": "the nurse", "text": "Plain author"},
            ]
        )
    ),
    "dosage_rate_quantity": _c(
        _base(
            dosage={
                "text": "5 mg orally",
                "site": {"coding": [{"system": SCT, "code": "368208006"}]},
                "route": {
                    "coding": [{"system": SCT, "code": "26643006"}],
                    "text": "Oral",
                },
                "method": {"text": "Swallow"},
                "dose": {"value": 5, "unit": "mg", "system": UCUM, "code": "mg"},
                "rateQuantity": {
                    "value": 2.5,
                    "unit": "mg/h",
                    "system": UCUM,
                    "code": "mg/h",
                },
            }
        )
    ),
    "dosage_rate_ratio": _c(
        _base(
            dosage={
                "dose": {"value": 5, "unit": "mg", "system": UCUM, "code": "mg"},
                "rateRatio": {
                    "numerator": {
                        "value": 5,
                        "unit": "mg",
                        "system": UCUM,
                        "code": "mg",
                    },
                    "denominator": {
                        "value": 1,
                        "unit": "h",
                        "system": UCUM,
                        "code": "h",
                    },
                },
            }
        )
    ),
    "extension": _c(
        _base(extension=[{"url": "http://example.org/ext", "valueString": "kept"}])
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_medication_administration_mapper_emits_valid_fhir_r4(case):
    assert_valid(
        pb2.MedicationAdministration, to_fhir_medication_administration(CASES[case])
    )


def test_mapper_serves_content_unchanged():
    content = _base(note=[{"text": "x"}])
    out = to_fhir_medication_administration(_c(content))
    assert out["resourceType"] == "MedicationAdministration"
    assert out["id"] == "580001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1; the integration tests cover that.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "in_progress"}),
        ("status as number", {"status": 1}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("instantiates as string", {"instantiates": "http://x"}),
        ("partOf as object", {"partOf": {"reference": "Procedure/1"}}),
        ("statusReason as object", {"statusReason": {"text": "x"}}),
        ("category as list", {"category": [{"text": "x"}]}),
        ("subject as string", {"subject": "Patient/1"}),
        ("context as string", {"context": "Encounter/1"}),
        (
            "supportingInformation as object",
            {"supportingInformation": {"reference": "x"}},
        ),
        ("effectiveDateTime as number", {"effectiveDateTime": 5}),
        ("effectiveDateTime not a dateTime", {"effectiveDateTime": "yesterday"}),
        ("effectivePeriod as string", {"effectivePeriod": "2026"}),
        (
            "performer as object",
            {"performer": {"actor": {"reference": "Practitioner/1"}}},
        ),
        ("performer entry as string", {"performer": ["x"]}),
        ("performer actor as string", {"performer": [{"actor": "Practitioner/1"}]}),
        ("reasonCode as object", {"reasonCode": {"text": "x"}}),
        (
            "reasonReference as object",
            {"reasonReference": {"reference": "Condition/1"}},
        ),
        ("request as list", {"request": [{"reference": "MedicationRequest/1"}]}),
        ("device as object", {"device": {"reference": "Device/1"}}),
        ("note as object", {"note": {"text": "x"}}),
        ("note time not a dateTime", {"note": [{"text": "x", "time": "later"}]}),
        ("dosage as list", {"dosage": [{"text": "x"}]}),
        ("dosage text as number", {"dosage": {"text": 5}}),
        ("dosage route as string", {"dosage": {"route": "oral"}}),
        ("dosage dose as string", {"dosage": {"dose": "5 mg"}}),
        ("eventHistory as object", {"eventHistory": {"reference": "Provenance/1"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "MedicationAdministration", "id": "580001", **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.MedicationAdministration, validate=True
        )

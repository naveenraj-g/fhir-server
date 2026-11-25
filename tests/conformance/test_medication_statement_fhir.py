"""FHIR R4 conformance for `to_fhir_medication_statement()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

MedicationStatement is stored whole in `content` (like MedicationRequest, QuestionnaireResponse
and the other content-based resources): the resource lives in MedicationStatementModel.content,
and to_fhir_medication_statement() only stamps `id` and `meta` onto it. So what can go wrong on
the read side is that stamping (e.g. a malformed meta extension) or a stored document the server
returns that isn't valid R4 - each case below is a `content` document as the write path would
store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.medication_statement import to_fhir_medication_statement
from app.models.medication_statement import MedicationStatementModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.medication_statement_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
SCT = "http://snomed.info/sct"
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
UCUM = "http://unitsofmeasure.org"


def _c(content: dict, **overrides) -> MedicationStatementModel:
    fields = {
        "medication_statement_id": 500001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return MedicationStatementModel(**fields)


def _base(**extra) -> dict:
    return {
        "status": "active",
        "medicationCodeableConcept": {"text": "Aspirin"},
        "subject": {"reference": "Patient/10001"},
        **extra,
    }


CASES = {
    "minimal": _c(_base()),
    "updated_by_and_updated_at": _c(_base(), updated_by="u-other", updated_at=D),
    **{
        f"status_{s}": _c(_base(status=s))
        for s in (
            "active",
            "completed",
            "entered-in-error",
            "intended",
            "stopped",
            "on-hold",
            "unknown",
            "not-taken",
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
                                "code": "RXN",
                            }
                        ]
                    },
                    "system": "https://fhir-server.dev/fhir/identifier-system/medication-statement-id",
                    "value": "MS-1",
                    "period": {"start": "2020-01-01"},
                    "assigner": {"reference": "Organization/190001"},
                },
                {"system": "urn:other", "value": "second"},
            ]
        )
    ),
    "based_on_and_part_of": _c(
        _base(
            basedOn=[
                {"reference": "MedicationRequest/90001"},
                {"reference": "CarePlan/290001"},
                {"reference": "ServiceRequest/80001"},
            ],
            partOf=[
                {"reference": "Observation/160001"},
                {"reference": "Procedure/100001"},
                {"reference": "MedicationStatement/500002"},
            ],
        )
    ),
    "status_reason_and_category": _c(
        _base(
            statusReason=[
                {"coding": [{"system": SCT, "code": "422587007"}], "text": "Nausea"}
            ],
            category={
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/medication-statement-category",
                        "code": "community",
                    }
                ]
            },
        )
    ),
    "medication_coded": _c(
        {
            "status": "active",
            "medicationCodeableConcept": {
                "coding": [
                    {"system": RXNORM, "code": "197361", "display": "Amlodipine"}
                ]
            },
            "subject": {"reference": "Patient/10001"},
        }
    ),
    "medication_reference": _c(
        {
            "status": "active",
            "medicationReference": {"reference": "Medication/250001"},
            "subject": {"reference": "Patient/10001"},
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
    "effective_date_time": _c(_base(effectiveDateTime="2026-02-03T08:30:00Z")),
    "effective_partial_date": _c(_base(effectiveDateTime="2026-02")),
    "effective_period": _c(
        _base(effectivePeriod={"start": "2026-01-01", "end": "2026-03-01"})
    ),
    "effective_open_period": _c(_base(effectivePeriod={"start": "2026-01-01"})),
    "date_asserted_and_source": _c(
        _base(
            dateAsserted="2026-01-15T10:05:00Z",
            informationSource={"reference": "Practitioner/30001"},
        )
    ),
    **{
        f"source_{t}": _c(_base(informationSource={"reference": f"{t}/1"}))
        for t in (
            "Patient",
            "Practitioner",
            "PractitionerRole",
            "RelatedPerson",
            "Organization",
        )
    },
    "derived_from": _c(
        _base(
            derivedFrom=[
                {"reference": "DocumentReference/320001"},
                {"reference": "https://other.example.org/fhir/Observation/9"},
            ]
        )
    ),
    "reason_code_and_reference": _c(
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
    "note": _c(
        _base(
            note=[
                {
                    "authorReference": {"reference": "Practitioner/30001"},
                    "time": "2026-01-15T10:06:00Z",
                    "text": "Takes it in the morning",
                },
                {"authorString": "the patient", "text": "Plain author"},
            ]
        )
    ),
    "dosage": _c(
        _base(
            dosage=[
                {
                    "sequence": 1,
                    "text": "5 mg once daily",
                    "additionalInstruction": [
                        {"coding": [{"system": SCT, "code": "311504000"}]}
                    ],
                    "patientInstruction": "With water",
                    "timing": {
                        "repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}
                    },
                    "asNeededBoolean": False,
                    "route": {"coding": [{"system": SCT, "code": "26643006"}]},
                    "method": {"text": "Swallow"},
                    "site": {"text": "Mouth"},
                    "doseAndRate": [
                        {
                            "type": {"text": "ordered"},
                            "doseQuantity": {
                                "value": 5,
                                "unit": "mg",
                                "system": UCUM,
                                "code": "mg",
                            },
                        }
                    ],
                    "maxDosePerPeriod": {
                        "numerator": {
                            "value": 10,
                            "unit": "mg",
                            "system": UCUM,
                            "code": "mg",
                        },
                        "denominator": {
                            "value": 1,
                            "unit": "d",
                            "system": UCUM,
                            "code": "d",
                        },
                    },
                    "maxDosePerAdministration": {
                        "value": 10,
                        "unit": "mg",
                        "system": UCUM,
                        "code": "mg",
                    },
                    "maxDosePerLifetime": {
                        "value": 300,
                        "unit": "mg",
                        "system": UCUM,
                        "code": "mg",
                    },
                },
                {"asNeededCodeableConcept": {"text": "pain"}},
            ]
        )
    ),
    "extension": _c(
        _base(extension=[{"url": "http://example.org/ext", "valueString": "kept"}])
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_medication_statement_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.MedicationStatement, to_fhir_medication_statement(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = _base(note=[{"text": "x"}])
    out = to_fhir_medication_statement(_c(content))
    assert out["resourceType"] == "MedicationStatement"
    assert out["id"] == "500001"
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
        ("status with an unknown code", {"status": "entered_in_error"}),
        ("status as number", {"status": 1}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("basedOn as object not a list", {"basedOn": {"reference": "CarePlan/1"}}),
        ("basedOn entry as string", {"basedOn": ["CarePlan/1"]}),
        ("partOf as object not a list", {"partOf": {"reference": "Observation/1"}}),
        ("statusReason as object", {"statusReason": {"text": "x"}}),
        ("category as list", {"category": [{"text": "x"}]}),
        ("subject as string", {"subject": "Patient/1"}),
        ("context as string", {"context": "Encounter/1"}),
        ("effectiveDateTime as number", {"effectiveDateTime": 5}),
        ("effectiveDateTime not a dateTime", {"effectiveDateTime": "yesterday"}),
        ("effectivePeriod as string", {"effectivePeriod": "2026"}),
        ("dateAsserted not a dateTime", {"dateAsserted": "yesterday"}),
        (
            "informationSource as list",
            {"informationSource": [{"reference": "Practitioner/1"}]},
        ),
        ("derivedFrom as object", {"derivedFrom": {"reference": "x"}}),
        ("reasonCode as object", {"reasonCode": {"text": "x"}}),
        (
            "reasonReference as object",
            {"reasonReference": {"reference": "Condition/1"}},
        ),
        ("note as object", {"note": {"text": "x"}}),
        ("note entry as string", {"note": ["x"]}),
        ("note time not a dateTime", {"note": [{"text": "x", "time": "later"}]}),
        ("dosage as object", {"dosage": {"text": "x"}}),
        ("dosage entry as string", {"dosage": ["x"]}),
        ("dosage sequence as string", {"dosage": [{"sequence": "one"}]}),
        ("dosage asNeededBoolean as string", {"dosage": [{"asNeededBoolean": "yes"}]}),
        ("dosage route as string", {"dosage": [{"route": "oral"}]}),
        ("dosage timing as list", {"dosage": [{"timing": [{"event": []}]}]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "MedicationStatement", "id": "500001", **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.MedicationStatement, validate=True
        )

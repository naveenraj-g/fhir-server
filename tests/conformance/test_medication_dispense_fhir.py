"""FHIR R4 conformance for `to_fhir_medication_dispense()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

MedicationDispense is stored whole in `content` (like MedicationAdministration, MedicationStatement
and the other content-based resources): the resource lives in MedicationDispenseModel.content, and
to_fhir_medication_dispense() only stamps `id` and `meta` onto it. So what can go wrong on the read
side is that stamping (e.g. a malformed meta extension) or a stored document the server returns
that isn't valid R4 - each case below is a `content` document as the write path would store it,
run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.medication_dispense import to_fhir_medication_dispense
from app.models.medication_dispense import MedicationDispenseModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.medication_dispense_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
SCT = "http://snomed.info/sct"
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
UCUM = "http://unitsofmeasure.org"


def _c(content: dict, **overrides) -> MedicationDispenseModel:
    fields = {
        "medication_dispense_id": 590001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return MedicationDispenseModel(**fields)


def _base(**extra) -> dict:
    return {
        "status": "completed",
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
            "preparation",
            "in-progress",
            "cancelled",
            "on-hold",
            "completed",
            "entered-in-error",
            "stopped",
            "declined",
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
                                "code": "DSP",
                            }
                        ]
                    },
                    "system": "https://fhir-server.dev/fhir/identifier-system/medication-dispense-id",
                    "value": "MD-1",
                    "period": {"start": "2020-01-01"},
                    "assigner": {"reference": "Organization/190001"},
                },
                {"system": "urn:other", "value": "second"},
            ]
        )
    ),
    "part_of": _c(_base(partOf=[{"reference": "Procedure/100001"}])),
    "status_reason_concept": _c(
        _base(
            status="cancelled",
            statusReasonCodeableConcept={
                "coding": [{"system": SCT, "code": "418309008"}],
                "text": "Out of stock",
            },
        )
    ),
    "status_reason_reference": _c(
        _base(
            status="cancelled",
            statusReasonReference={"reference": "DetectedIssue/540001"},
        )
    ),
    "category": _c(
        _base(
            category={
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/medicationdispense-category",
                        "code": "outpatient",
                    }
                ]
            }
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
        }
    ),
    "no_subject": _c(
        {"status": "completed", "medicationCodeableConcept": {"text": "Aspirin"}}
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
    **{
        f"performer_{t}": _c(_base(performer=[{"actor": {"reference": f"{t}/1"}}]))
        for t in (
            "Practitioner",
            "PractitionerRole",
            "Organization",
            "Patient",
            "Device",
            "RelatedPerson",
        )
    },
    "performer_with_function": _c(
        _base(
            performer=[
                {
                    "function": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/medicationdispense-performer-function",
                                "code": "packager",
                            }
                        ]
                    },
                    "actor": {"reference": "Practitioner/30001"},
                }
            ]
        )
    ),
    "location_prescription_type": _c(
        _base(
            location={"reference": "Location/230001"},
            authorizingPrescription=[
                {"reference": "MedicationRequest/90001"},
                {"reference": "MedicationRequest/90002"},
            ],
            type={
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                        "code": "FF",
                    }
                ]
            },
        )
    ),
    "quantities": _c(
        _base(
            quantity={"value": 30, "unit": "tablet"},
            daysSupply={"value": 30, "unit": "Day", "system": UCUM, "code": "d"},
        )
    ),
    "dates": _c(
        _base(
            whenPrepared="2026-01-15T09:00:00Z", whenHandedOver="2026-01-15T10:00:00Z"
        )
    ),
    "partial_dates": _c(_base(whenPrepared="2026-01", whenHandedOver="2026")),
    "destination_and_receiver": _c(
        _base(
            destination={"reference": "Location/230002"},
            receiver=[
                {"reference": "Patient/10001"},
                {"reference": "Practitioner/30001"},
            ],
        )
    ),
    "note": _c(
        _base(
            note=[
                {
                    "authorReference": {"reference": "Practitioner/30001"},
                    "time": "2026-01-15T10:06:00Z",
                    "text": "Counselled",
                },
                {"authorString": "the pharmacist", "text": "Plain author"},
            ]
        )
    ),
    "dosage_instruction": _c(
        _base(
            dosageInstruction=[
                {
                    "sequence": 1,
                    "text": "1 tablet daily",
                    "timing": {
                        "repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}
                    },
                    "asNeededBoolean": False,
                    "route": {"coding": [{"system": SCT, "code": "26643006"}]},
                    "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}],
                },
                {"asNeededCodeableConcept": {"text": "pain"}},
            ]
        )
    ),
    "substitution": _c(
        _base(
            substitution={
                "wasSubstituted": True,
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ActSubstanceAdminSubstitutionCode",
                            "code": "E",
                        }
                    ]
                },
                "reason": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-ActReason",
                                "code": "FP",
                            }
                        ]
                    }
                ],
                "responsibleParty": [
                    {"reference": "Practitioner/30001"},
                    {"reference": "PractitionerRole/140001"},
                ],
            }
        )
    ),
    "detected_issue_and_event_history": _c(
        _base(
            detectedIssue=[{"reference": "DetectedIssue/540001"}],
            eventHistory=[{"reference": "Provenance/270001"}],
        )
    ),
    "extension": _c(
        _base(extension=[{"url": "http://example.org/ext", "valueString": "kept"}])
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_medication_dispense_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.MedicationDispense, to_fhir_medication_dispense(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = _base(note=[{"text": "x"}])
    out = to_fhir_medication_dispense(_c(content))
    assert out["resourceType"] == "MedicationDispense"
    assert out["id"] == "590001"
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
        ("partOf as object", {"partOf": {"reference": "Procedure/1"}}),
        ("category as list", {"category": [{"text": "x"}]}),
        ("subject as string", {"subject": "Patient/1"}),
        ("context as string", {"context": "Encounter/1"}),
        (
            "supportingInformation as object",
            {"supportingInformation": {"reference": "x"}},
        ),
        (
            "performer as object",
            {"performer": {"actor": {"reference": "Practitioner/1"}}},
        ),
        ("performer entry as string", {"performer": ["x"]}),
        ("performer actor as string", {"performer": [{"actor": "Practitioner/1"}]}),
        ("location as list", {"location": [{"reference": "Location/1"}]}),
        (
            "authorizingPrescription as object",
            {"authorizingPrescription": {"reference": "x"}},
        ),
        ("type as list", {"type": [{"text": "x"}]}),
        ("quantity as string", {"quantity": "30"}),
        ("daysSupply value as string", {"daysSupply": {"value": "thirty"}}),
        ("whenPrepared not a dateTime", {"whenPrepared": "yesterday"}),
        ("whenHandedOver as number", {"whenHandedOver": 5}),
        ("destination as list", {"destination": [{"reference": "Location/1"}]}),
        ("receiver as object", {"receiver": {"reference": "Patient/1"}}),
        ("note as object", {"note": {"text": "x"}}),
        ("note time not a dateTime", {"note": [{"text": "x", "time": "later"}]}),
        ("dosageInstruction as object", {"dosageInstruction": {"text": "x"}}),
        (
            "dosageInstruction sequence as string",
            {"dosageInstruction": [{"sequence": "one"}]},
        ),
        ("substitution as list", {"substitution": [{"wasSubstituted": True}]}),
        (
            "substitution wasSubstituted as string",
            {"substitution": {"wasSubstituted": "yes"}},
        ),
        (
            "substitution reason as object",
            {"substitution": {"wasSubstituted": True, "reason": {"text": "x"}}},
        ),
        (
            "detectedIssue as object",
            {"detectedIssue": {"reference": "DetectedIssue/1"}},
        ),
        ("eventHistory as object", {"eventHistory": {"reference": "Provenance/1"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "MedicationDispense", "id": "590001", **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.MedicationDispense, validate=True
        )

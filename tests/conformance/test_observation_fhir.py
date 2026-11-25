"""FHIR R4 conformance for `to_fhir_observation()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Observation is stored Medplum-style (like Patient, Appointment, Encounter, Condition, Procedure,
DiagnosticReport, RiskAssessment and the other content-based resources): the resource lives whole
in ObservationModel.content, and to_fhir_observation() only stamps `id` and `meta` onto it. So what
can go wrong on the read side is that stamping (e.g. a malformed meta extension) or a stored
document the server returns that isn't valid R4 — each case below is a `content` document as the
write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.observation import to_fhir_observation
from app.models.observation import ObservationModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.observation_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
LOINC = "http://loinc.org"
SCT = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"
CODE = {
    "coding": [{"system": LOINC, "code": "85354-9", "display": "Blood pressure panel"}]
}
BASE = {"status": "final", "code": CODE}


def _qty(value, unit="mmHg", code="mm[Hg]"):
    return {"value": value, "unit": unit, "system": UCUM, "code": code}


def _observation(content: dict, **overrides) -> ObservationModel:
    fields = {
        "observation_id": 160001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return ObservationModel(**fields)


def _with(**elements) -> ObservationModel:
    return _observation({**BASE, **elements})


CASES = {
    "minimal": _with(),
    "updated_by_and_updated_at": _observation(
        dict(BASE), updated_by="u-other", updated_at=D
    ),
    "identifier_with_type_and_assigner": _with(
        identifier=[
            {
                "use": "official",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "FILL",
                        }
                    ]
                },
                "system": "https://fhir-server.dev/fhir/identifier-system/observation-id",
                "value": "OBS-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    **{
        f"status_{s}": _observation({"status": s, "code": CODE})
        for s in (
            "registered",
            "preliminary",
            "final",
            "amended",
            "corrected",
            "cancelled",
            "entered-in-error",
            "unknown",
        )
    },
    **{
        f"based_on_{t}": _with(basedOn=[{"reference": f"{t}/1"}])
        for t in (
            "CarePlan",
            "DeviceRequest",
            "ImmunizationRecommendation",
            "MedicationRequest",
            "NutritionOrder",
            "ServiceRequest",
        )
    },
    **{
        f"part_of_{t}": _with(partOf=[{"reference": f"{t}/1"}])
        for t in (
            "MedicationAdministration",
            "MedicationDispense",
            "MedicationStatement",
            "Procedure",
            "Immunization",
            "ImagingStudy",
        )
    },
    "category": _with(
        category=[
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "vital-signs",
                    }
                ]
            },
            {"text": "other"},
        ]
    ),
    **{
        f"subject_{t}": _with(subject={"reference": f"{t}/1"})
        for t in ("Patient", "Group", "Device", "Location")
    },
    "subject_with_display": _with(
        subject={"reference": "Patient/10001", "display": "A. Patient"}
    ),
    "subject_logical": _with(
        subject={"identifier": {"system": "urn:pts", "value": "P-9"}}
    ),
    "subject_absolute_url": _with(
        subject={"reference": "https://other.example.org/fhir/Patient/9"}
    ),
    "focus": _with(
        focus=[{"reference": "Condition/120001"}, {"reference": "Specimen/1"}]
    ),
    "encounter": _with(encounter={"reference": "Encounter/20001"}),
    "effective_date_time": _with(effectiveDateTime="2023-01-15T09:30:00Z"),
    "effective_date_time_partial": _with(effectiveDateTime="2023-01"),
    "effective_period": _with(
        effectivePeriod={"start": "2023-01-01", "end": "2023-06-01"}
    ),
    "effective_instant": _with(effectiveInstant="2023-01-15T09:30:00Z"),
    "effective_timing": _with(
        effectiveTiming={
            "event": ["2023-01-01T08:00:00Z"],
            "repeat": {"frequency": 1, "period": 1, "periodUnit": "d"},
        }
    ),
    "issued": _with(issued="2023-01-15T09:35:00Z"),
    **{
        f"performer_{t}": _with(performer=[{"reference": f"{t}/1"}])
        for t in (
            "Practitioner",
            "PractitionerRole",
            "Organization",
            "CareTeam",
            "Patient",
            "RelatedPerson",
        )
    },
    "value_quantity": _with(valueQuantity=_qty(120)),
    "value_quantity_comparator": _with(valueQuantity={**_qty(5), "comparator": "<"}),
    "value_codeable_concept": _with(
        valueCodeableConcept={
            "coding": [{"system": SCT, "code": "260385009"}],
            "text": "Negative",
        }
    ),
    "value_string": _with(valueString="positive"),
    "value_boolean": _with(valueBoolean=False),
    "value_integer": _with(valueInteger=7),
    "value_range": _with(valueRange={"low": _qty(1), "high": _qty(2)}),
    "value_ratio": _with(
        valueRatio={
            "numerator": _qty(1, "mg", "mg"),
            "denominator": _qty(2, "mL", "mL"),
        }
    ),
    "value_sampled_data": _with(
        valueSampledData={
            "origin": _qty(0),
            "period": 10,
            "dimensions": 1,
            "data": "1 2 3",
        }
    ),
    "value_time": _with(valueTime="09:30:00"),
    "value_date_time": _with(valueDateTime="2023-01"),
    "value_period": _with(valuePeriod={"start": "2023-01-01", "end": "2023-06-01"}),
    "data_absent_reason": _with(
        dataAbsentReason={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/data-absent-reason",
                    "code": "unknown",
                }
            ]
        }
    ),
    "interpretation": _with(
        interpretation=[
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                        "code": "H",
                    }
                ]
            }
        ]
    ),
    "note_author_string": _with(
        note=[
            {
                "text": "Taken seated.",
                "time": "2023-01-15T10:00:00Z",
                "authorString": "Nurse Joy",
            }
        ]
    ),
    "note_author_reference": _with(
        note=[{"text": "n", "authorReference": {"reference": "Practitioner/30001"}}]
    ),
    "body_site_and_method": _with(
        bodySite={"coding": [{"system": SCT, "code": "368208006"}]},
        method={"coding": [{"system": SCT, "code": "37931006"}]},
    ),
    "specimen_and_device": _with(
        specimen={"reference": "Specimen/1"}, device={"reference": "DeviceMetric/1"}
    ),
    "reference_range": _with(
        referenceRange=[
            {
                "low": _qty(90),
                "high": _qty(140),
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/referencerange-meaning",
                            "code": "normal",
                        }
                    ]
                },
                "appliesTo": [{"text": "Adults"}],
                "age": {
                    "low": {"value": 18, "unit": "yr", "system": UCUM, "code": "a"}
                },
                "text": "90-140 mmHg",
            },
            {"text": "text only"},
        ]
    ),
    **{
        f"has_member_{t}": _with(hasMember=[{"reference": f"{t}/1"}])
        for t in ("Observation", "QuestionnaireResponse", "MolecularSequence")
    },
    **{
        f"derived_from_{t}": _with(derivedFrom=[{"reference": f"{t}/1"}])
        for t in (
            "DocumentReference",
            "ImagingStudy",
            "Media",
            "QuestionnaireResponse",
            "Observation",
            "MolecularSequence",
        )
    },
    "component_code_only": _with(component=[{"code": CODE}]),
    "component_blood_pressure": _with(
        component=[
            {
                "code": {"coding": [{"system": LOINC, "code": "8480-6"}]},
                "valueQuantity": _qty(142),
                "interpretation": [{"text": "high"}],
                "referenceRange": [{"high": _qty(140)}],
            },
            {
                "code": {"coding": [{"system": LOINC, "code": "8462-4"}]},
                "valueQuantity": _qty(91),
            },
        ]
    ),
    "component_value_choices": _with(
        component=[
            {"code": {"text": "a"}, "valueCodeableConcept": {"text": "x"}},
            {"code": {"text": "b"}, "valueString": "y"},
            {"code": {"text": "c"}, "valueBoolean": True},
            {"code": {"text": "d"}, "valueInteger": 3},
            {"code": {"text": "e"}, "valueRange": {"low": _qty(1)}},
            {"code": {"text": "f"}, "valueRatio": {"numerator": _qty(1)}},
            {"code": {"text": "g"}, "valueTime": "10:00:00"},
            {"code": {"text": "h"}, "valueDateTime": "2023-01-01"},
            {"code": {"text": "i"}, "valuePeriod": {"start": "2023-01-01"}},
        ]
    ),
    "component_data_absent_reason": _with(
        component=[
            {
                "code": {"text": "a"},
                "dataAbsentReason": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/data-absent-reason",
                            "code": "unknown",
                        }
                    ]
                },
            }
        ]
    ),
    "extension": _with(
        extension=[
            {
                "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                "valueString": "y",
            }
        ]
    ),
    "full": _with(
        identifier=[{"system": "urn:obs", "value": "OBS-1"}],
        category=[{"text": "vital"}],
        subject={"reference": "Patient/10001"},
        encounter={"reference": "Encounter/20001"},
        effectiveDateTime="2023-01-15T09:30:00Z",
        issued="2023-01-15T09:35:00Z",
        performer=[{"reference": "Practitioner/30001"}],
        valueQuantity=_qty(120),
        interpretation=[{"text": "H"}],
        note=[{"text": "n"}],
        bodySite={"text": "arm"},
        method={"text": "auscultation"},
        referenceRange=[{"high": _qty(140)}],
        hasMember=[{"reference": "Observation/160002"}],
        derivedFrom=[{"reference": "Media/7"}],
        component=[{"code": {"text": "a"}, "valueQuantity": _qty(1)}],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_observation_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.Observation, to_fhir_observation(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {
        **BASE,
        "valueQuantity": _qty(120),
        "component": [{"code": {"text": "a"}}],
    }
    out = to_fhir_observation(_observation(content))
    assert out["resourceType"] == "Observation"
    assert out["id"] == "160001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — `subject`, `code` or `encounter` as a one-item list; nor
# rules obs-3, obs-6, obs-7; the integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("subject as string not a Reference", {"subject": "Patient/1"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("code as string not a CodeableConcept", {"code": "x"}),
        ("effectiveDateTime not a dateTime", {"effectiveDateTime": "yesterday"}),
        ("effectivePeriod as string", {"effectivePeriod": "2023"}),
        (
            "effectiveInstant without a time zone",
            {"effectiveInstant": "2023-01-15T09:30:00"},
        ),
        ("issued not an instant", {"issued": "yesterday"}),
        ("encounter as string not a Reference", {"encounter": "Encounter/1"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("category as object not a list", {"category": {"text": "x"}}),
        (
            "performer as object not a list",
            {"performer": {"reference": "Practitioner/1"}},
        ),
        (
            "basedOn as object not a list",
            {"basedOn": {"reference": "ServiceRequest/1"}},
        ),
        ("valueQuantity as string", {"valueQuantity": "5"}),
        ("valueQuantity value as string", {"valueQuantity": {"value": "high"}}),
        (
            "valueQuantity comparator unknown",
            {"valueQuantity": {"value": 1, "comparator": "~"}},
        ),
        ("valueCodeableConcept as string", {"valueCodeableConcept": "x"}),
        ("valueString as number", {"valueString": 5}),
        ("valueBoolean as string", {"valueBoolean": "yes"}),
        ("valueInteger as string", {"valueInteger": "7"}),
        ("valueRange low as number", {"valueRange": {"low": 5}}),
        ("valueTime not a time", {"valueTime": "noon"}),
        ("valueDateTime not a dateTime", {"valueDateTime": "yesterday"}),
        ("valuePeriod as string", {"valuePeriod": "2023"}),
        ("dataAbsentReason as string", {"dataAbsentReason": "unknown"}),
        ("interpretation as object not a list", {"interpretation": {"text": "H"}}),
        ("note as object not a list", {"note": {"text": "x"}}),
        ("bodySite as string", {"bodySite": "arm"}),
        ("method as string", {"method": "x"}),
        ("specimen as string", {"specimen": "Specimen/1"}),
        ("referenceRange as object not a list", {"referenceRange": {"text": "x"}}),
        ("referenceRange low as number", {"referenceRange": [{"low": 5}]}),
        (
            "hasMember as object not a list",
            {"hasMember": {"reference": "Observation/1"}},
        ),
        ("derivedFrom as object not a list", {"derivedFrom": {"reference": "Media/1"}}),
        ("component as object not a list", {"component": {"code": {"text": "x"}}}),
        ("component code as string", {"component": [{"code": "x"}]}),
        (
            "component valueQuantity as string",
            {"component": [{"code": {"text": "x"}, "valueQuantity": "5"}]},
        ),
        (
            "component interpretation as string",
            {"component": [{"code": {"text": "x"}, "interpretation": "H"}]},
        ),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Observation", "id": "160001", **BASE, **broken}
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.Observation, validate=True
        )

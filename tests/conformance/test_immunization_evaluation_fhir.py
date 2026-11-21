"""FHIR R4 conformance for `to_fhir_immunization_evaluation()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

ImmunizationEvaluation is stored Medplum-style (like Patient, Appointment, Encounter,
Condition, Procedure, DiagnosticReport, Immunization and the other content-based
resources): the resource lives whole in ImmunizationEvaluationModel.content, and
to_fhir_immunization_evaluation() only stamps `id` and `meta` onto it. So what can go wrong
on the read side is that stamping (e.g. a malformed meta extension) or a stored document the
server returns that isn't valid R4 — each case below is a `content` document as the write
path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.immunization_evaluation import to_fhir_immunization_evaluation
from app.models.immunization_evaluation import ImmunizationEvaluationModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.immunization_evaluation_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
PATIENT = {"reference": "Patient/10001"}
EVENT = {"reference": "Immunization/330001"}
SCT = "http://snomed.info/sct"
TARGET = {"coding": [{"system": SCT, "code": "6142004", "display": "Influenza"}]}
DOSE = {
    "coding": [
        {
            "system": "http://terminology.hl7.org/CodeSystem/immunization-evaluation-dose-status",
            "code": "valid",
        }
    ]
}
BASE = {
    "status": "completed",
    "patient": PATIENT,
    "targetDisease": TARGET,
    "immunizationEvent": EVENT,
    "doseStatus": DOSE,
}


def _evaluation(content: dict, **overrides) -> ImmunizationEvaluationModel:
    fields = {
        "immunization_evaluation_id": 610001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return ImmunizationEvaluationModel(**fields)


def _with(**elements) -> ImmunizationEvaluationModel:
    return _evaluation({**BASE, **elements})


CASES = {
    "minimal": _with(),
    "updated_by_and_updated_at": _evaluation(
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
                "system": "https://fhir-server.dev/fhir/identifier-system/immunization-evaluation-id",
                "value": "IE-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    **{f"status_{s}": _with(status=s) for s in ("completed", "entered-in-error")},
    "patient_with_display": _with(
        patient={"reference": "Patient/10001", "display": "A. Patient"}
    ),
    "patient_logical": _with(
        patient={"identifier": {"system": "urn:pts", "value": "P-9"}}
    ),
    "patient_absolute_url": _with(
        patient={"reference": "https://other.example.org/fhir/Patient/9"}
    ),
    "date": _with(date="2023-01-15T09:30:00Z"),
    "date_partial": _with(date="2023-01"),
    "authority": _with(authority={"reference": "Organization/190001"}),
    "target_disease_text_only": _with(targetDisease={"text": "Tetanus"}),
    "immunization_event_logical": _with(
        immunizationEvent={"identifier": {"system": "urn:imm", "value": "I-9"}}
    ),
    "immunization_event_absolute_url": _with(
        immunizationEvent={"reference": "https://other.example.org/fhir/Immunization/3"}
    ),
    "dose_status_text_only": _with(doseStatus={"text": "Too early"}),
    "dose_status_reason": _with(
        doseStatusReason=[
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/immunization-evaluation-dose-status-reason",
                        "code": "agedoses",
                    }
                ]
            },
            {"text": "Other"},
        ]
    ),
    "description_and_series": _with(
        description="Evaluated against the seasonal flu schedule", series="Seasonal"
    ),
    "dose_numbers_positive_int": _with(
        doseNumberPositiveInt=1, seriesDosesPositiveInt=2
    ),
    "dose_numbers_string": _with(doseNumberString="booster", seriesDosesString="many"),
    "extension": _with(
        extension=[
            {
                "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                "valueString": "y",
            }
        ]
    ),
    "full": _with(
        identifier=[{"system": "urn:ie", "value": "IE-1"}],
        date="2023-01-15T09:30:00Z",
        authority={"reference": "Organization/190001"},
        doseStatusReason=[{"text": "Age"}],
        description="Notes",
        series="Seasonal",
        doseNumberPositiveInt=1,
        seriesDosesPositiveInt=1,
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_immunization_evaluation_mapper_emits_valid_fhir_r4(case):
    assert_valid(
        pb2.ImmunizationEvaluation, to_fhir_immunization_evaluation(CASES[case])
    )


def test_mapper_serves_content_unchanged():
    content = {
        **BASE,
        "authority": {"reference": "Organization/190001"},
        "series": "Seasonal",
    }
    out = to_fhir_immunization_evaluation(_evaluation(content))
    assert out["resourceType"] == "ImmunizationEvaluation"
    assert out["id"] == "610001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — `patient`, `targetDisease` or `doseStatus` as a one-item
# list; the integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("patient as string not a Reference", {"patient": "Patient/1"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("date not a dateTime", {"date": "yesterday"}),
        ("date as number", {"date": 20230115}),
        ("authority as string not a Reference", {"authority": "Organization/1"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("targetDisease as string not a CodeableConcept", {"targetDisease": "6142004"}),
        (
            "immunizationEvent as string not a Reference",
            {"immunizationEvent": "Immunization/1"},
        ),
        ("doseStatus as string not a CodeableConcept", {"doseStatus": "valid"}),
        ("doseStatusReason as object not a list", {"doseStatusReason": {"text": "x"}}),
        ("description as number", {"description": 5}),
        ("series as number", {"series": 5}),
        ("doseNumberPositiveInt not a positiveInt", {"doseNumberPositiveInt": "one"}),
        (
            "seriesDosesPositiveInt not a positiveInt",
            {"seriesDosesPositiveInt": "many"},
        ),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "ImmunizationEvaluation",
        "id": "610001",
        **BASE,
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.ImmunizationEvaluation, validate=True
        )

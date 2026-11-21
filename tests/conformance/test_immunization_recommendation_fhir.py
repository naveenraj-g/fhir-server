"""FHIR R4 conformance for `to_fhir_immunization_recommendation()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

ImmunizationRecommendation is stored Medplum-style (like Patient, Appointment, Encounter,
Condition, Procedure, DiagnosticReport, Immunization and the other content-based
resources): the resource lives whole in ImmunizationRecommendationModel.content, and
to_fhir_immunization_recommendation() only stamps `id` and `meta` onto it. So what can go
wrong on the read side is that stamping (e.g. a malformed meta extension) or a stored
document the server returns that isn't valid R4 — each case below is a `content` document
as the write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.immunization_recommendation import (
    to_fhir_immunization_recommendation,
)
from app.models.immunization_recommendation import ImmunizationRecommendationModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.immunization_recommendation_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
PATIENT = {"reference": "Patient/10001"}
DATE = "2023-01-15T09:30:00Z"
SCT = "http://snomed.info/sct"
STATUS = "http://terminology.hl7.org/CodeSystem/immunization-recommendation-status"
DUE = {"coding": [{"system": STATUS, "code": "due", "display": "Due"}]}
FLU = {
    "coding": [
        {"system": "http://hl7.org/fhir/sid/cvx", "code": "140", "display": "Influenza"}
    ]
}


def _recommendation(content: dict, **overrides) -> ImmunizationRecommendationModel:
    fields = {
        "immunization_recommendation_id": 510001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return ImmunizationRecommendationModel(**fields)


def _with(**elements) -> ImmunizationRecommendationModel:
    return _recommendation(
        {
            "patient": PATIENT,
            "date": DATE,
            "recommendation": [{"vaccineCode": [FLU], "forecastStatus": DUE}],
            **elements,
        }
    )


def _entry(**elements) -> ImmunizationRecommendationModel:
    """A recommendation whose single entry carries `elements` besides forecastStatus/vaccineCode."""
    return _with(
        recommendation=[{"vaccineCode": [FLU], "forecastStatus": DUE, **elements}]
    )


CASES = {
    "minimal": _with(),
    "updated_by_and_updated_at": _recommendation(
        {
            "patient": PATIENT,
            "date": DATE,
            "recommendation": [{"vaccineCode": [FLU], "forecastStatus": DUE}],
        },
        updated_by="u-other",
        updated_at=D,
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
                "system": "https://fhir-server.dev/fhir/identifier-system/immunization-recommendation-id",
                "value": "IR-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "patient_with_display": _with(
        patient={"reference": "Patient/10001", "display": "A. Patient"}
    ),
    "patient_logical": _with(
        patient={"identifier": {"system": "urn:pts", "value": "P-9"}}
    ),
    "patient_absolute_url": _with(
        patient={"reference": "https://other.example.org/fhir/Patient/9"}
    ),
    "date_partial": _with(date="2023-01"),
    "authority": _with(authority={"reference": "Organization/190001"}),
    "target_disease_only": _with(
        recommendation=[
            {
                "targetDisease": {"coding": [{"system": SCT, "code": "6142004"}]},
                "forecastStatus": DUE,
            }
        ]
    ),
    "vaccine_code_text_only": _with(
        recommendation=[{"vaccineCode": [{"text": "Tetanus"}], "forecastStatus": DUE}]
    ),
    "forecast_status_text_only": _with(
        recommendation=[{"vaccineCode": [FLU], "forecastStatus": {"text": "Complete"}}]
    ),
    "several_vaccine_codes": _entry(
        vaccineCode=[
            FLU,
            {"coding": [{"system": "http://hl7.org/fhir/sid/cvx", "code": "03"}]},
        ]
    ),
    "contraindicated_vaccine_code": _entry(
        contraindicatedVaccineCode=[
            {"coding": [{"system": "http://hl7.org/fhir/sid/cvx", "code": "99"}]}
        ]
    ),
    "forecast_reason": _entry(
        forecastReason=[
            {"coding": [{"system": "http://reason", "code": "seasonal"}]},
            {"text": "Other"},
        ]
    ),
    "date_criterion": _entry(
        dateCriterion=[
            {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "30980-7",
                            "display": "Date vaccine due",
                        }
                    ]
                },
                "value": "2023-06-01T00:00:00Z",
            },
            {"code": {"text": "Overdue"}, "value": "2023-09-01"},
        ]
    ),
    "description_and_series": _entry(
        description="Seasonal flu shot", series="Seasonal"
    ),
    "dose_numbers_positive_int": _entry(
        doseNumberPositiveInt=1, seriesDosesPositiveInt=2
    ),
    "dose_numbers_string": _entry(doseNumberString="booster", seriesDosesString="many"),
    **{
        f"supporting_immunization_{t}": _entry(
            supportingImmunization=[{"reference": f"{t}/1"}]
        )
        for t in ("Immunization", "ImmunizationEvaluation")
    },
    "supporting_immunization_logical": _entry(
        supportingImmunization=[{"identifier": {"system": "urn:imm", "value": "I-9"}}]
    ),
    "supporting_patient_information": _entry(
        supportingPatientInformation=[
            {"reference": "Observation/160001"},
            {"reference": "Condition/120001"},
            {"reference": "Procedure/100001"},
        ]
    ),
    "several_recommendations": _with(
        recommendation=[
            {"vaccineCode": [FLU], "forecastStatus": DUE},
            {
                "targetDisease": {"coding": [{"system": SCT, "code": "14189004"}]},
                "forecastStatus": {
                    "coding": [{"system": STATUS, "code": "contraindicated"}]
                },
            },
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
        identifier=[{"system": "urn:ir", "value": "IR-1"}],
        authority={"reference": "Organization/190001"},
        recommendation=[
            {
                "vaccineCode": [FLU],
                "targetDisease": {"coding": [{"system": SCT, "code": "6142004"}]},
                "contraindicatedVaccineCode": [{"text": "Egg allergy"}],
                "forecastStatus": DUE,
                "forecastReason": [{"text": "Seasonal"}],
                "dateCriterion": [{"code": {"text": "Due"}, "value": "2023-06-01"}],
                "description": "Seasonal flu shot",
                "series": "Seasonal",
                "doseNumberPositiveInt": 1,
                "seriesDosesPositiveInt": 1,
                "supportingImmunization": [{"reference": "Immunization/330001"}],
                "supportingPatientInformation": [{"reference": "Condition/120001"}],
            }
        ],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_immunization_recommendation_mapper_emits_valid_fhir_r4(case):
    assert_valid(
        pb2.ImmunizationRecommendation, to_fhir_immunization_recommendation(CASES[case])
    )


def test_mapper_serves_content_unchanged():
    content = {
        "patient": PATIENT,
        "date": DATE,
        "recommendation": [{"vaccineCode": [FLU], "forecastStatus": DUE}],
        "authority": {"reference": "Organization/190001"},
    }
    out = to_fhir_immunization_recommendation(_recommendation(content))
    assert out["resourceType"] == "ImmunizationRecommendation"
    assert out["id"] == "510001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — `patient`, `authority` or `targetDisease` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("patient as string not a Reference", {"patient": "Patient/1"}),
        ("date not a dateTime", {"date": "yesterday"}),
        ("date as number", {"date": 20230115}),
        ("authority as string not a Reference", {"authority": "Organization/1"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        (
            "recommendation as object not a list",
            {"recommendation": {"forecastStatus": DUE}},
        ),
        (
            "recommendation forecastStatus as string",
            {"recommendation": [{"vaccineCode": [FLU], "forecastStatus": "due"}]},
        ),
        (
            "recommendation vaccineCode as object not a list",
            {"recommendation": [{"vaccineCode": FLU, "forecastStatus": DUE}]},
        ),
        (
            "recommendation description as number",
            {
                "recommendation": [
                    {"vaccineCode": [FLU], "forecastStatus": DUE, "description": 5}
                ]
            },
        ),
        (
            "recommendation dose number not a positiveInt",
            {
                "recommendation": [
                    {
                        "vaccineCode": [FLU],
                        "forecastStatus": DUE,
                        "doseNumberPositiveInt": "one",
                    }
                ]
            },
        ),
        (
            "dateCriterion value not a dateTime",
            {
                "recommendation": [
                    {
                        "vaccineCode": [FLU],
                        "forecastStatus": DUE,
                        "dateCriterion": [{"code": {"text": "x"}, "value": "soon"}],
                    }
                ]
            },
        ),
        (
            "dateCriterion as object not a list",
            {
                "recommendation": [
                    {
                        "vaccineCode": [FLU],
                        "forecastStatus": DUE,
                        "dateCriterion": {"code": {"text": "x"}, "value": "2023-01-01"},
                    }
                ]
            },
        ),
        (
            "supportingImmunization as object not a list",
            {
                "recommendation": [
                    {
                        "vaccineCode": [FLU],
                        "forecastStatus": DUE,
                        "supportingImmunization": {"reference": "Immunization/1"},
                    }
                ]
            },
        ),
        (
            "supportingPatientInformation as string",
            {
                "recommendation": [
                    {
                        "vaccineCode": [FLU],
                        "forecastStatus": DUE,
                        "supportingPatientInformation": ["Observation/1"],
                    }
                ]
            },
        ),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "ImmunizationRecommendation",
        "id": "510001",
        "patient": PATIENT,
        "date": DATE,
        "recommendation": [{"vaccineCode": [FLU], "forecastStatus": DUE}],
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.ImmunizationRecommendation, validate=True
        )

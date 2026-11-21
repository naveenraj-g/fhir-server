"""FHIR R4 conformance for `to_fhir_risk_assessment()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

RiskAssessment is stored Medplum-style (like Patient, Appointment, Encounter, Condition,
Procedure, DiagnosticReport, Immunization and the other content-based resources): the resource
lives whole in RiskAssessmentModel.content, and to_fhir_risk_assessment() only stamps `id` and
`meta` onto it. So what can go wrong on the read side is that stamping (e.g. a malformed meta
extension) or a stored document the server returns that isn't valid R4 — each case below is a
`content` document as the write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.risk_assessment import to_fhir_risk_assessment
from app.models.risk_assessment import RiskAssessmentModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.risk_assessment_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
SUBJECT = {"reference": "Patient/10001"}
SCT = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"
BASE = {"status": "final", "subject": SUBJECT}
RISK = {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/risk-probability", "code": "moderate"}]}


def _pct(value):
    return {"value": value, "unit": "%", "system": UCUM, "code": "%"}


def _assessment(content: dict, **overrides) -> RiskAssessmentModel:
    fields = {
        "risk_assessment_id": 520001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return RiskAssessmentModel(**fields)


def _with(**elements) -> RiskAssessmentModel:
    return _assessment({**BASE, **elements})


def _prediction(**elements) -> RiskAssessmentModel:
    return _with(prediction=[elements])


CASES = {
    "minimal": _with(),
    "updated_by_and_updated_at": _assessment(dict(BASE), updated_by="u-other", updated_at=D),
    "identifier_with_type_and_assigner": _with(
        identifier=[
            {
                "use": "official",
                "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "FILL"}]},
                "system": "https://fhir-server.dev/fhir/identifier-system/risk-assessment-id",
                "value": "RA-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    **{
        f"status_{s}": _assessment({**BASE, "status": s})
        for s in ("registered", "preliminary", "final", "amended", "corrected", "cancelled", "entered-in-error",
                  "unknown")
    },
    "based_on_and_parent": _with(basedOn={"reference": "ServiceRequest/80001"}, parent={"reference": "Procedure/100001"}),
    "method_and_code": _with(
        method={"coding": [{"system": SCT, "code": "225338004"}], "text": "Risk assessment"},
        code={"coding": [{"system": SCT, "code": "709510001"}]},
    ),
    **{
        f"subject_{t}": _assessment({"status": "final", "subject": {"reference": f"{t}/1"}})
        for t in ("Patient", "Group")
    },
    "subject_with_display": _with(subject={"reference": "Patient/10001", "display": "A. Patient"}),
    "subject_logical": _with(subject={"identifier": {"system": "urn:pts", "value": "P-9"}}),
    "subject_absolute_url": _with(subject={"reference": "https://other.example.org/fhir/Patient/9"}),
    "encounter_and_condition": _with(
        encounter={"reference": "Encounter/20001"}, condition={"reference": "Condition/120001"}
    ),
    "occurrence_date_time": _with(occurrenceDateTime="2023-01-15T09:30:00Z"),
    "occurrence_date_time_partial": _with(occurrenceDateTime="2023-01"),
    "occurrence_period": _with(occurrencePeriod={"start": "2023-01-01", "end": "2023-06-01"}),
    **{f"performer_{t}": _with(performer={"reference": f"{t}/1"}) for t in ("Practitioner", "PractitionerRole", "Device")},
    "performer_logical": _with(performer={"identifier": {"system": "urn:who", "value": "W-1"}}),
    "reason_code": _with(reasonCode=[{"coding": [{"system": SCT, "code": "160303001"}]}, {"text": "Other"}]),
    **{
        f"reason_reference_{t}": _with(reasonReference=[{"reference": f"{t}/1"}])
        for t in ("Condition", "Observation", "DiagnosticReport", "DocumentReference")
    },
    "basis": _with(basis=[{"reference": "Observation/160001"}, {"reference": "Condition/120001"}]),
    "prediction_minimal": _with(prediction=[{}]),
    "prediction_outcome": _prediction(outcome={"coding": [{"system": SCT, "code": "54329005"}]}),
    "prediction_probability_decimal": _prediction(probabilityDecimal=12.5),
    "prediction_probability_range": _prediction(probabilityRange={"low": _pct(5), "high": _pct(10)}),
    "prediction_probability_range_open": _prediction(probabilityRange={"low": _pct(50)}),
    "prediction_qualitative_risk": _prediction(qualitativeRisk=RISK),
    "prediction_relative_risk": _prediction(relativeRisk=1.4),
    "prediction_when_period": _prediction(whenPeriod={"start": "2023-01-01", "end": "2033-01-01"}),
    "prediction_when_range": _prediction(
        whenRange={"low": {"value": 40, "unit": "yr", "system": UCUM, "code": "a"},
                   "high": {"value": 50, "unit": "yr", "system": UCUM, "code": "a"}}
    ),
    "prediction_rationale": _prediction(rationale="Based on lipid panel and blood pressure."),
    "several_predictions": _with(
        prediction=[{"probabilityDecimal": 12.5, "qualitativeRisk": RISK}, {"probabilityRange": {"low": _pct(1)}}]
    ),
    "mitigation": _with(mitigation="Statin therapy and lifestyle changes."),
    "note_author_string": _with(note=[{"text": "Reassess in 12 months.", "time": "2023-01-15T10:00:00Z", "authorString": "Nurse Joy"}]),
    "note_author_reference": _with(note=[{"text": "n", "authorReference": {"reference": "Practitioner/30001"}}]),
    "extension": _with(extension=[{"url": "https://fhir-server.dev/fhir/StructureDefinition/x", "valueString": "y"}]),
    "full": _with(
        identifier=[{"system": "urn:ra", "value": "RA-1"}],
        method={"text": "Framingham"},
        code={"text": "CVD risk"},
        encounter={"reference": "Encounter/20001"},
        occurrenceDateTime="2023-01-15T09:30:00Z",
        condition={"reference": "Condition/120001"},
        performer={"reference": "Practitioner/30001"},
        reasonCode=[{"text": "Family history"}],
        reasonReference=[{"reference": "Condition/120001"}],
        basis=[{"reference": "Observation/160001"}],
        prediction=[{"outcome": {"text": "MI"}, "probabilityDecimal": 12.5, "qualitativeRisk": RISK,
                     "relativeRisk": 1.4, "whenPeriod": {"start": "2023-01-01"}, "rationale": "Lipids"}],
        mitigation="Statins",
        note=[{"text": "n"}],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_risk_assessment_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.RiskAssessment, to_fhir_risk_assessment(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {**BASE, "mitigation": "Statins", "prediction": [{"probabilityDecimal": 12.5}]}
    out = to_fhir_risk_assessment(_assessment(content))
    assert out["resourceType"] == "RiskAssessment"
    assert out["id"] == "520001"
    assert {k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")} == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — `subject`, `method` or `performer` as a one-item list; the
# integration tests cover what they can. Nor rules ras-1 / ras-2.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("subject as string not a Reference", {"subject": "Patient/1"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("method as string not a CodeableConcept", {"method": "x"}),
        ("code as string not a CodeableConcept", {"code": "x"}),
        ("occurrenceDateTime not a dateTime", {"occurrenceDateTime": "yesterday"}),
        ("occurrencePeriod as string", {"occurrencePeriod": "2023"}),
        ("condition as string not a Reference", {"condition": "Condition/1"}),
        ("performer as string not a Reference", {"performer": "Practitioner/1"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("reasonCode as object not a list", {"reasonCode": {"text": "x"}}),
        ("reasonReference as object not a list", {"reasonReference": {"reference": "Condition/1"}}),
        ("basis as object not a list", {"basis": {"reference": "Observation/1"}}),
        ("prediction as object not a list", {"prediction": {"probabilityDecimal": 5}}),
        ("prediction probabilityDecimal as string", {"prediction": [{"probabilityDecimal": "high"}]}),
        ("prediction probabilityRange low as number", {"prediction": [{"probabilityRange": {"low": 5}}]}),
        ("prediction qualitativeRisk as string", {"prediction": [{"qualitativeRisk": "low"}]}),
        ("prediction relativeRisk as string", {"prediction": [{"relativeRisk": "twice"}]}),
        ("prediction whenPeriod as string", {"prediction": [{"whenPeriod": "2023"}]}),
        ("prediction rationale as number", {"prediction": [{"rationale": 5}]}),
        ("mitigation as number", {"mitigation": 5}),
        ("note as object not a list", {"note": {"text": "x"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "RiskAssessment", "id": "520001", **BASE, **broken}
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(fhir_json_text(payload), pb2.RiskAssessment, validate=True)

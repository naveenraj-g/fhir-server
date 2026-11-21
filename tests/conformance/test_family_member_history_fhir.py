"""FHIR R4 conformance for `to_fhir_family_member_history()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

FamilyMemberHistory is stored Medplum-style (like Patient, Appointment, Encounter, Condition,
Procedure, DiagnosticReport, Immunization and the other content-based resources): the resource
lives whole in FamilyMemberHistoryModel.content, and to_family_member_history() only stamps `id`
and `meta` onto it. So what can go wrong on the read side is that stamping (e.g. a malformed
meta extension) or a stored document the server returns that isn't valid R4 — each case below
is a `content` document as the write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.family_member_history import to_fhir_family_member_history
from app.models.family_member_history import FamilyMemberHistoryModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.family_member_history_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
PATIENT = {"reference": "Patient/10001"}
SCT = "http://snomed.info/sct"
MOTHER = {
    "coding": [
        {
            "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
            "code": "MTH",
            "display": "mother",
        }
    ]
}
DIABETES = {
    "coding": [
        {"system": SCT, "code": "44054006", "display": "Type 2 diabetes mellitus"}
    ]
}
BASE = {"status": "completed", "patient": PATIENT, "relationship": MOTHER}
AGE = {"value": 70, "unit": "a", "system": "http://unitsofmeasure.org", "code": "a"}


def _history(content: dict, **overrides) -> FamilyMemberHistoryModel:
    fields = {
        "family_member_history_id": 490001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return FamilyMemberHistoryModel(**fields)


def _with(**elements) -> FamilyMemberHistoryModel:
    return _history({**BASE, **elements})


def _condition(**elements) -> FamilyMemberHistoryModel:
    return _with(condition=[{"code": DIABETES, **elements}])


CASES = {
    "minimal": _with(),
    "updated_by_and_updated_at": _history(
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
                "system": "https://fhir-server.dev/fhir/identifier-system/family-member-history-id",
                "value": "FMH-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    **{
        f"status_{s}": _with(status=s)
        for s in ("partial", "completed", "entered-in-error", "health-unknown")
    },
    "data_absent_reason": _with(
        status="health-unknown",
        dataAbsentReason={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/history-absent-reason",
                    "code": "withheld",
                }
            ]
        },
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
    "instantiates_canonical_and_uri": _with(
        instantiatesCanonical=[
            "http://example.org/fhir/PlanDefinition/fh|1.0",
            "Questionnaire/5",
        ],
        instantiatesUri=["http://example.org/protocols/fh"],
    ),
    "date_name_and_sex": _with(
        date="2023-01-15T09:30:00Z",
        name="Mary Windsor",
        sex={
            "coding": [
                {
                    "system": "http://hl7.org/fhir/administrative-gender",
                    "code": "female",
                }
            ]
        },
    ),
    "date_partial": _with(date="2023-01"),
    "relationship_text_only": _with(relationship={"text": "Aunt"}),
    "born_period": _with(bornPeriod={"start": "1950-01-01", "end": "1951-01-01"}),
    "born_date": _with(bornDate="1950-03-12"),
    "born_string": _with(bornString="around 1950"),
    "age_age_estimated": _with(ageAge=AGE, estimatedAge=True),
    "age_age_with_comparator": _with(ageAge={**AGE, "comparator": ">"}),
    "age_range": _with(ageRange={"low": AGE, "high": {**AGE, "value": 80}}),
    "age_string": _with(ageString="elderly"),
    "deceased_boolean": _with(deceasedBoolean=True),
    "deceased_age": _with(deceasedAge=AGE),
    "deceased_range": _with(deceasedRange={"low": AGE, "high": {**AGE, "value": 80}}),
    "deceased_date": _with(deceasedDate="2010-05-01"),
    "deceased_string": _with(deceasedString="in the war"),
    "reason_code": _with(
        reasonCode=[
            {"coding": [{"system": SCT, "code": "160303001"}]},
            {"text": "Other"},
        ]
    ),
    **{
        f"reason_reference_{t}": _with(reasonReference=[{"reference": f"{t}/1"}])
        for t in (
            "Condition",
            "Observation",
            "AllergyIntolerance",
            "QuestionnaireResponse",
            "DiagnosticReport",
            "DocumentReference",
        )
    },
    "note_author_string": _with(
        note=[
            {
                "text": "Since her forties",
                "time": "2023-01-15T10:00:00Z",
                "authorString": "Nurse Joy",
            }
        ]
    ),
    "note_author_reference": _with(
        note=[{"text": "n", "authorReference": {"reference": "Practitioner/30001"}}]
    ),
    "condition_minimal": _condition(),
    "condition_outcome_and_death": _condition(
        outcome={"coding": [{"system": SCT, "code": "6736007"}]},
        contributedToDeath=True,
    ),
    "condition_onset_age": _condition(onsetAge=AGE),
    "condition_onset_range": _condition(
        onsetRange={"low": AGE, "high": {**AGE, "value": 60}}
    ),
    "condition_onset_period": _condition(
        onsetPeriod={"start": "1990-01-01", "end": "1991-01-01"}
    ),
    "condition_onset_string": _condition(onsetString="childhood"),
    "condition_note": _condition(
        note=[
            {
                "text": "Insulin from 55",
                "authorReference": {"reference": "Practitioner/30001"},
            }
        ]
    ),
    "several_conditions": _with(
        condition=[{"code": DIABETES}, {"code": {"text": "Hypertension"}}]
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
        identifier=[{"system": "urn:fmh", "value": "FMH-1"}],
        instantiatesUri=["http://example.org/protocols/fh"],
        date="2023-01-15T09:30:00Z",
        name="Mary Windsor",
        sex={"text": "Female"},
        ageAge=AGE,
        estimatedAge=True,
        deceasedBoolean=False,
        reasonCode=[{"text": "Diabetes"}],
        reasonReference=[{"reference": "Condition/120001"}],
        note=[{"text": "n"}],
        condition=[
            {
                "code": DIABETES,
                "outcome": {"text": "Moderate"},
                "contributedToDeath": False,
                "onsetAge": AGE,
                "note": [{"text": "c"}],
            }
        ],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_family_member_history_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.FamilyMemberHistory, to_fhir_family_member_history(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {**BASE, "name": "Mary Windsor", "ageAge": AGE}
    out = to_fhir_family_member_history(_history(content))
    assert out["resourceType"] == "FamilyMemberHistory"
    assert out["id"] == "490001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — `patient`, `relationship` or `sex` as a one-item list; the
# integration tests cover what they can. Nor rules fhs-1 / fhs-2.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("patient as string not a Reference", {"patient": "Patient/1"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("relationship as string not a CodeableConcept", {"relationship": "MTH"}),
        ("sex as string not a CodeableConcept", {"sex": "female"}),
        ("date not a dateTime", {"date": "yesterday"}),
        ("name as number", {"name": 5}),
        ("bornDate not a date", {"bornDate": "long ago"}),
        ("ageAge as string", {"ageAge": "70"}),
        ("estimatedAge as string", {"estimatedAge": "yes"}),
        ("deceasedBoolean as string", {"deceasedBoolean": "no"}),
        ("deceasedDate not a date", {"deceasedDate": "once"}),
        (
            "instantiatesCanonical as string not a list",
            {"instantiatesCanonical": "http://x"},
        ),
        ("instantiatesUri as string not a list", {"instantiatesUri": "http://x"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("reasonCode as object not a list", {"reasonCode": {"text": "x"}}),
        (
            "reasonReference as object not a list",
            {"reasonReference": {"reference": "Condition/1"}},
        ),
        ("note as object not a list", {"note": {"text": "x"}}),
        ("condition as object not a list", {"condition": {"code": DIABETES}}),
        ("condition code as string", {"condition": [{"code": "44054006"}]}),
        (
            "condition contributedToDeath as string",
            {"condition": [{"code": DIABETES, "contributedToDeath": "yes"}]},
        ),
        (
            "condition onsetAge as string",
            {"condition": [{"code": DIABETES, "onsetAge": "42"}]},
        ),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "FamilyMemberHistory", "id": "490001", **BASE, **broken}
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.FamilyMemberHistory, validate=True
        )

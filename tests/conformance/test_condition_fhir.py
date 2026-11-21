"""FHIR R4 conformance for `to_fhir_condition()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Condition is stored Medplum-style (like Patient, Appointment, Encounter and the
other content-based resources): the resource lives whole in
ConditionModel.content, and to_fhir_condition() only stamps `id` and `meta` onto
it. So what can go wrong on the read side is that stamping (e.g. a malformed meta
extension) or a stored document the server returns that isn't valid R4 — each
case below is a `content` document as the write path would store it, run through
the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.condition import to_fhir_condition
from app.models.condition import ConditionModel

from .support import assert_valid, fhir_json_text

condition_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.condition_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
SUBJECT = {"reference": "Patient/10001"}
SCT = "http://snomed.info/sct"
CLIN = "http://terminology.hl7.org/CodeSystem/condition-clinical"
VERIF = "http://terminology.hl7.org/CodeSystem/condition-ver-status"
CAT = "http://terminology.hl7.org/CodeSystem/condition-category"


def _condition(content: dict, **overrides) -> ConditionModel:
    fields = {
        "condition_id": 120001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return ConditionModel(**fields)


def _with(**elements) -> ConditionModel:
    return _condition({"subject": SUBJECT, **elements})


def _clinical(code):
    return {"coding": [{"system": CLIN, "code": code}]}


_AGE = {
    "value": 12,
    "unit": "years",
    "system": "http://unitsofmeasure.org",
    "code": "a",
}
_RANGE = {"low": {"value": 5, "unit": "years"}, "high": {"value": 10, "unit": "years"}}

CASES = {
    "minimal": _with(),
    "updated_by_and_updated_at": _condition(
        {"subject": SUBJECT}, updated_by="u-other", updated_at=D
    ),
    "identifier_with_type_and_assigner": _with(
        identifier=[
            {
                "use": "official",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "PRN",
                        }
                    ]
                },
                "system": "https://fhir-server.dev/fhir/identifier-system/condition-id",
                "value": "C-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    **{
        f"clinical_status_{c}": _with(clinicalStatus=_clinical(c))
        for c in (
            "active",
            "recurrence",
            "relapse",
            "inactive",
            "remission",
            "resolved",
        )
    },
    **{
        f"verification_status_{v}": _with(
            verificationStatus={"coding": [{"system": VERIF, "code": v}]},
            **(
                {}
                if v == "entered-in-error"
                else {"clinicalStatus": _clinical("active")}
            ),
        )
        for v in (
            "unconfirmed",
            "provisional",
            "differential",
            "confirmed",
            "refuted",
            "entered-in-error",
        )
    },
    "category_both": _with(
        category=[
            {"coding": [{"system": CAT, "code": "problem-list-item"}]},
            {"coding": [{"system": CAT, "code": "encounter-diagnosis"}]},
        ]
    ),
    "severity": _with(
        severity={
            "coding": [{"system": SCT, "code": "24484000", "display": "Severe"}],
            "text": "Severe",
        }
    ),
    "code": _with(
        code={
            "coding": [{"system": SCT, "code": "38341003", "display": "Hypertension"}],
            "text": "HTN",
        }
    ),
    "body_site": _with(
        bodySite=[
            {"coding": [{"system": SCT, "code": "368208006"}]},
            {"text": "Left arm"},
        ]
    ),
    "subject_with_display": _with(
        subject={"reference": "Patient/10001", "display": "A. Patient"}
    ),
    "subject_group": _condition({"subject": {"reference": "Group/5"}}),
    "subject_logical": _condition(
        {"subject": {"identifier": {"system": "urn:pts", "value": "P-9"}}}
    ),
    "subject_absolute_url": _condition(
        {"subject": {"reference": "https://other.example.org/fhir/Patient/9"}}
    ),
    "encounter": _with(encounter={"reference": "Encounter/20001"}),
    "onset_date_time": _with(onsetDateTime="2023-01-15T09:30:00Z"),
    "onset_date_time_partial": _with(onsetDateTime="2023-01"),
    "onset_age": _with(onsetAge=_AGE),
    "onset_period": _with(onsetPeriod={"start": "2020-01-01", "end": "2020-02-01"}),
    "onset_range": _with(onsetRange=_RANGE),
    "onset_string": _with(onsetString="as a child"),
    "abatement_date_time": _with(
        abatementDateTime="2024-05-01", clinicalStatus=_clinical("resolved")
    ),
    "abatement_age": _with(abatementAge=_AGE, clinicalStatus=_clinical("remission")),
    "abatement_period": _with(
        abatementPeriod={"start": "2024-01-01"}, clinicalStatus=_clinical("inactive")
    ),
    "abatement_range": _with(
        abatementRange=_RANGE, clinicalStatus=_clinical("resolved")
    ),
    "abatement_string": _with(
        abatementString="resolved by itself", clinicalStatus=_clinical("resolved")
    ),
    "recorded_date": _with(recordedDate="2023-01-15T10:00:00Z"),
    **{
        f"recorder_{t}": _with(recorder={"reference": f"{t}/1"})
        for t in ("Practitioner", "PractitionerRole", "Patient", "RelatedPerson")
    },
    **{
        f"asserter_{t}": _with(asserter={"reference": f"{t}/1"})
        for t in ("Practitioner", "PractitionerRole", "Patient", "RelatedPerson")
    },
    "asserter_logical": _with(
        asserter={"identifier": {"system": "urn:who", "value": "W-1"}}
    ),
    "stage_summary": _with(
        stage=[{"summary": {"coding": [{"system": SCT, "code": "14803004"}]}}]
    ),
    "stage_assessment_and_type": _with(
        stage=[
            {
                "assessment": [{"reference": "Observation/160001"}],
                "type": {"text": "clinical"},
            }
        ]
    ),
    "evidence_code": _with(
        evidence=[
            {
                "code": [
                    {"coding": [{"system": SCT, "code": "29857009"}]},
                    {"text": "Cough"},
                ]
            }
        ]
    ),
    "evidence_detail": _with(
        evidence=[
            {
                "detail": [
                    {"reference": "Observation/160001"},
                    {"reference": "Encounter/1"},
                ]
            }
        ]
    ),
    "note_author_reference": _with(
        note=[
            {
                "authorReference": {"reference": "Practitioner/30001"},
                "time": "2023-01-15T10:05:00Z",
                "text": "Hives",
            }
        ]
    ),
    "note_author_string": _with(note=[{"authorString": "Dr Smith", "text": "Hives"}]),
    "extension": _with(
        extension=[
            {
                "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                "valueString": "y",
            }
        ]
    ),
    "full": _with(
        identifier=[{"system": "urn:c", "value": "C-1"}],
        clinicalStatus=_clinical("active"),
        verificationStatus={"coding": [{"system": VERIF, "code": "confirmed"}]},
        category=[{"coding": [{"system": CAT, "code": "problem-list-item"}]}],
        severity={"coding": [{"system": SCT, "code": "24484000"}]},
        code={"coding": [{"system": SCT, "code": "38341003"}]},
        bodySite=[{"coding": [{"system": SCT, "code": "368208006"}]}],
        encounter={"reference": "Encounter/20001"},
        onsetDateTime="2023-01-15T09:30:00Z",
        recordedDate="2023-01-15T10:00:00Z",
        recorder={"reference": "Practitioner/30001"},
        asserter={"reference": "Patient/10001"},
        stage=[{"summary": {"coding": [{"system": SCT, "code": "14803004"}]}}],
        evidence=[
            {
                "code": [{"coding": [{"system": SCT, "code": "29857009"}]}],
                "detail": [{"reference": "Observation/160001"}],
            }
        ],
        note=[{"text": "Hives"}],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_condition_mapper_emits_valid_fhir_r4(case):
    assert_valid(condition_pb2.Condition, to_fhir_condition(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {
        "subject": SUBJECT,
        "clinicalStatus": _clinical("active"),
        "recordedDate": "2023",
    }
    out = to_fhir_condition(_condition(content))
    assert out["resourceType"] == "Condition"
    assert out["id"] == "120001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — `subject` as a one-item list — and rules con-3 /
# con-4 / con-5, which tie clinicalStatus to verificationStatus, category and
# abatement[x]; the integration tests cover what they can and the java_validator
# backend enforces the rest.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("subject as string not a Reference", {"subject": "Patient/1"}),
        (
            "clinicalStatus as string not a CodeableConcept",
            {"clinicalStatus": "active"},
        ),
        ("category as object not a list", {"category": {"text": "x"}}),
        ("bodySite as object not a list", {"bodySite": {"text": "x"}}),
        ("recordedDate not a dateTime", {"recordedDate": "tomorrow"}),
        ("onsetDateTime not a dateTime", {"onsetDateTime": "yesterday"}),
        ("abatementDateTime not a dateTime", {"abatementDateTime": "soon"}),
        ("onsetAge value as string", {"onsetAge": {"value": "twelve"}}),
        ("onsetString as number", {"onsetString": 5}),
        ("stage as object not a list", {"stage": {"summary": {"text": "x"}}}),
        ("evidence as object not a list", {"evidence": {"code": [{"text": "x"}]}}),
        ("evidence detail as string", {"evidence": [{"detail": "Observation/1"}]}),
        ("note as object not a list", {"note": {"text": "x"}}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "Condition",
        "id": "120001",
        "subject": SUBJECT,
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), condition_pb2.Condition, validate=True
        )

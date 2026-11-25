"""FHIR R4 conformance for `to_fhir_detected_issue()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

DetectedIssue is stored Medplum-style (like Patient, Appointment, Encounter, Condition,
Procedure, DiagnosticReport, RiskAssessment, ClinicalImpression and the other content-based
resources): the resource lives whole in DetectedIssueModel.content, and to_fhir_detected_issue()
only stamps `id` and `meta` onto it. So what can go wrong on the read side is that stamping
(e.g. a malformed meta extension) or a stored document the server returns that isn't valid R4 —
each case below is a `content` document as the write path would store it, run through the real
read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.detected_issue import to_fhir_detected_issue
from app.models.detected_issue import DetectedIssueModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.detected_issue_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
ACT = "http://terminology.hl7.org/CodeSystem/v3-ActCode"
BASE = {"status": "final"}


def _issue(content: dict, **overrides) -> DetectedIssueModel:
    fields = {
        "detected_issue_id": 540001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return DetectedIssueModel(**fields)


def _with(**elements) -> DetectedIssueModel:
    return _issue({**BASE, **elements})


CASES = {
    "minimal": _with(),
    "updated_by_and_updated_at": _issue(dict(BASE), updated_by="u-other", updated_at=D),
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
                "system": "https://fhir-server.dev/fhir/identifier-system/detected-issue-id",
                "value": "DI-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    **{
        f"status_{s}": _issue({"status": s})
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
    "code": _with(
        code={
            "coding": [
                {"system": ACT, "code": "DUPTHPY", "display": "Duplicate therapy alert"}
            ],
            "text": "Dup",
        }
    ),
    **{f"severity_{s}": _with(severity=s) for s in ("high", "moderate", "low")},
    "patient": _with(patient={"reference": "Patient/10001"}),
    "patient_with_display": _with(
        patient={"reference": "Patient/10001", "display": "A. Patient"}
    ),
    "patient_logical": _with(
        patient={"identifier": {"system": "urn:pts", "value": "P-9"}}
    ),
    "patient_absolute_url": _with(
        patient={"reference": "https://other.example.org/fhir/Patient/9"}
    ),
    "identified_date_time": _with(identifiedDateTime="2023-01-15T09:30:00Z"),
    "identified_date_time_partial": _with(identifiedDateTime="2023-01"),
    "identified_period": _with(
        identifiedPeriod={"start": "2023-01-01", "end": "2023-06-01"}
    ),
    "identified_period_open": _with(identifiedPeriod={"start": "2023-01-01"}),
    **{
        f"author_{t}": _with(author={"reference": f"{t}/1"})
        for t in ("Practitioner", "PractitionerRole", "Device")
    },
    "author_logical": _with(
        author={"identifier": {"system": "urn:who", "value": "W-1"}}
    ),
    **{
        f"implicated_{t}": _with(implicated=[{"reference": f"{t}/1"}])
        for t in (
            "Condition",
            "MedicationRequest",
            "Observation",
            "Patient",
            "ClinicalImpression",
        )
    },
    "implicated_several": _with(
        implicated=[{"reference": "Condition/1"}, {"reference": "MedicationRequest/2"}]
    ),
    "evidence_empty": _with(evidence=[{}]),
    "evidence_code": _with(
        evidence=[
            {
                "code": [
                    {"coding": [{"system": "http://snomed.info/sct", "code": "1"}]},
                    {"text": "x"},
                ]
            }
        ]
    ),
    "evidence_detail": _with(
        evidence=[
            {
                "detail": [
                    {"reference": "DiagnosticReport/110001"},
                    {"reference": "GuidanceResponse/1"},
                ]
            }
        ]
    ),
    "evidence_both": _with(
        evidence=[{"code": [{"text": "x"}], "detail": [{"reference": "Observation/1"}]}]
    ),
    "detail": _with(detail="The patient is prescribed two drugs of the same class."),
    "reference": _with(reference="http://example.org/protocols/duplicate-therapy"),
    "mitigation_action": _with(mitigation=[{"action": {"text": "Stopped"}}]),
    "mitigation_full": _with(
        mitigation=[
            {
                "action": {
                    "coding": [{"system": ACT, "code": "13"}],
                    "text": "Stopped",
                },
                "date": "2023-01-16T08:00:00Z",
                "author": {"reference": "Practitioner/30001"},
            }
        ]
    ),
    "mitigation_author_role": _with(
        mitigation=[
            {"action": {"text": "a"}, "author": {"reference": "PractitionerRole/1"}}
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
        identifier=[{"system": "urn:di", "value": "DI-1"}],
        code={"text": "Dup"},
        severity="high",
        patient={"reference": "Patient/10001"},
        identifiedDateTime="2023-01-15T09:30:00Z",
        author={"reference": "Practitioner/30001"},
        implicated=[{"reference": "Condition/120001"}],
        evidence=[
            {
                "code": [{"text": "x"}],
                "detail": [{"reference": "DiagnosticReport/110001"}],
            }
        ],
        detail="Two drugs of one class.",
        reference="http://example.org/protocols/a",
        mitigation=[
            {
                "action": {"text": "Stopped"},
                "date": "2023-01-16",
                "author": {"reference": "Practitioner/30001"},
            }
        ],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_detected_issue_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.DetectedIssue, to_fhir_detected_issue(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {
        **BASE,
        "detail": "Two drugs of one class.",
        "evidence": [{"code": [{"text": "x"}]}],
    }
    out = to_fhir_detected_issue(_issue(content))
    assert out["resourceType"] == "DetectedIssue"
    assert out["id"] == "540001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — `patient`, `code` or `author` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("patient as string not a Reference", {"patient": "Patient/1"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("severity with an unknown code", {"severity": "critical"}),
        ("code as string not a CodeableConcept", {"code": "x"}),
        ("identifiedDateTime not a dateTime", {"identifiedDateTime": "yesterday"}),
        ("identifiedPeriod as string", {"identifiedPeriod": "2023"}),
        ("author as string not a Reference", {"author": "Practitioner/1"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        (
            "implicated as object not a list",
            {"implicated": {"reference": "Condition/1"}},
        ),
        ("evidence as object not a list", {"evidence": {"detail": []}}),
        ("evidence code as string", {"evidence": [{"code": "x"}]}),
        (
            "evidence detail as object not a list",
            {"evidence": [{"detail": {"reference": "Observation/1"}}]},
        ),
        ("detail as number", {"detail": 5}),
        ("reference as number", {"reference": 5}),
        ("mitigation as object not a list", {"mitigation": {"action": {"text": "x"}}}),
        ("mitigation action as string", {"mitigation": [{"action": "x"}]}),
        (
            "mitigation date not a dateTime",
            {"mitigation": [{"action": {"text": "x"}, "date": "yesterday"}]},
        ),
        (
            "mitigation author as string",
            {"mitigation": [{"action": {"text": "x"}, "author": "Practitioner/1"}]},
        ),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "DetectedIssue", "id": "540001", **BASE, **broken}
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.DetectedIssue, validate=True
        )

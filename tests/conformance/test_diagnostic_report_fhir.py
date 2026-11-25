"""FHIR R4 conformance for `to_fhir_diagnostic_report()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

DiagnosticReport is stored Medplum-style (like Patient, Appointment, Encounter,
Condition, Procedure and the other content-based resources): the resource lives
whole in DiagnosticReportModel.content, and to_fhir_diagnostic_report() only
stamps `id` and `meta` onto it. So what can go wrong on the read side is that
stamping (e.g. a malformed meta extension) or a stored document the server returns
that isn't valid R4 — each case below is a `content` document as the write path
would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.diagnostic_report import to_fhir_diagnostic_report
from app.models.diagnostic_report import DiagnosticReportModel

from .support import assert_valid, fhir_json_text

report_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.diagnostic_report_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
SUBJECT = {"reference": "Patient/10001"}
CODE = {
    "coding": [
        {"system": "http://loinc.org", "code": "58410-2", "display": "CBC panel"}
    ]
}
SCT = "http://snomed.info/sct"


def _report(content: dict, **overrides) -> DiagnosticReportModel:
    fields = {
        "diagnostic_report_id": 110001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return DiagnosticReportModel(**fields)


def _with(**elements) -> DiagnosticReportModel:
    return _report({"status": "final", "code": CODE, "subject": SUBJECT, **elements})


CASES = {
    "minimal": _with(),
    "updated_by_and_updated_at": _report(
        {"status": "final", "code": CODE}, updated_by="u-other", updated_at=D
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
                "system": "https://fhir-server.dev/fhir/identifier-system/report-id",
                "value": "DR-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    **{
        f"status_{s}": _report({"status": s, "code": CODE, "subject": SUBJECT})
        for s in (
            "registered",
            "partial",
            "preliminary",
            "final",
            "amended",
            "corrected",
            "appended",
            "cancelled",
            "entered-in-error",
            "unknown",
        )
    },
    **{
        f"based_on_{t}": _with(basedOn=[{"reference": f"{t}/1"}])
        for t in (
            "CarePlan",
            "ImmunizationRecommendation",
            "MedicationRequest",
            "NutritionOrder",
            "ServiceRequest",
        )
    },
    "category": _with(
        category=[
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "LAB",
                    }
                ],
                "text": "Lab",
            },
            {"text": "Other"},
        ]
    ),
    "code_with_text": _with(
        code={
            "coding": [{"system": "http://loinc.org", "code": "58410-2"}],
            "text": "CBC",
        }
    ),
    **{
        f"subject_{t}": _report(
            {"status": "final", "code": CODE, "subject": {"reference": f"{t}/1"}}
        )
        for t in ("Patient", "Group", "Device", "Location")
    },
    "subject_with_display": _with(
        subject={"reference": "Patient/10001", "display": "A. Patient"}
    ),
    "subject_logical": _report(
        {
            "status": "final",
            "code": CODE,
            "subject": {"identifier": {"system": "urn:pts", "value": "P-9"}},
        }
    ),
    "subject_absolute_url": _report(
        {
            "status": "final",
            "code": CODE,
            "subject": {"reference": "https://other.example.org/fhir/Patient/9"},
        }
    ),
    "no_subject": _report({"status": "final", "code": CODE}),
    "encounter": _with(encounter={"reference": "Encounter/20001"}),
    "effective_date_time": _with(effectiveDateTime="2023-01-15T09:30:00Z"),
    "effective_date_time_partial": _with(effectiveDateTime="2023-01"),
    "effective_period": _with(
        effectivePeriod={"start": "2020-01-01", "end": "2020-02-01"}
    ),
    "effective_period_open": _with(effectivePeriod={"start": "2020-01-01"}),
    "issued": _with(issued="2023-01-15T12:00:00Z"),
    **{
        f"performer_{t}": _with(performer=[{"reference": f"{t}/1"}])
        for t in ("Practitioner", "PractitionerRole", "Organization", "CareTeam")
    },
    "performer_logical": _with(
        performer=[{"identifier": {"system": "urn:who", "value": "W-1"}}]
    ),
    "results_interpreter": _with(
        resultsInterpreter=[
            {"reference": "Practitioner/30001"},
            {"reference": "Organization/190001"},
        ]
    ),
    "specimen": _with(
        specimen=[{"reference": "Specimen/310001"}, {"reference": "Specimen/310002"}]
    ),
    "result": _with(result=[{"reference": "Observation/160001"}]),
    "imaging_study": _with(imagingStudy=[{"reference": "ImagingStudy/5"}]),
    "media": _with(
        media=[
            {"comment": "Slide 1", "link": {"reference": "Media/9"}},
            {"link": {"reference": "Media/10"}},
        ]
    ),
    "conclusion": _with(conclusion="Normal blood count."),
    "conclusion_code": _with(
        conclusionCode=[
            {"coding": [{"system": SCT, "code": "17621005"}]},
            {"text": "Borderline"},
        ]
    ),
    "presented_form": _with(
        presentedForm=[
            {
                "contentType": "application/pdf",
                "url": "https://example.org/report.pdf",
                "title": "Report",
            },
            {
                "contentType": "text/plain",
                "language": "en",
                "data": "SGVsbG8=",
                "size": 5,
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
        identifier=[{"system": "urn:dr", "value": "DR-1"}],
        basedOn=[{"reference": "ServiceRequest/80001"}],
        category=[
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                        "code": "LAB",
                    }
                ]
            }
        ],
        encounter={"reference": "Encounter/20001"},
        effectivePeriod={
            "start": "2023-01-15T09:30:00Z",
            "end": "2023-01-15T10:00:00Z",
        },
        issued="2023-01-15T12:00:00Z",
        performer=[{"reference": "Practitioner/30001"}],
        resultsInterpreter=[{"reference": "Practitioner/30001"}],
        specimen=[{"reference": "Specimen/310001"}],
        result=[{"reference": "Observation/160001"}],
        media=[{"link": {"reference": "Media/9"}}],
        conclusion="Normal.",
        conclusionCode=[{"coding": [{"system": SCT, "code": "17621005"}]}],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_diagnostic_report_mapper_emits_valid_fhir_r4(case):
    assert_valid(report_pb2.DiagnosticReport, to_fhir_diagnostic_report(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {
        "status": "final",
        "code": CODE,
        "subject": SUBJECT,
        "issued": "2023-01-15T12:00:00Z",
    }
    out = to_fhir_diagnostic_report(_report(content))
    assert out["resourceType"] == "DiagnosticReport"
    assert out["id"] == "110001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — `subject` or `code` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("subject as string not a Reference", {"subject": "Patient/1"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("code as string not a CodeableConcept", {"code": "58410-2"}),
        ("category as object not a list", {"category": {"text": "x"}}),
        ("effectiveDateTime not a dateTime", {"effectiveDateTime": "yesterday"}),
        ("issued not an instant", {"issued": "2023-01-15"}),
        (
            "performer as object not a list",
            {"performer": {"reference": "Practitioner/1"}},
        ),
        ("performer as string", {"performer": ["Practitioner/1"]}),
        (
            "resultsInterpreter as object not a list",
            {"resultsInterpreter": {"reference": "Practitioner/1"}},
        ),
        ("specimen as object not a list", {"specimen": {"reference": "Specimen/1"}}),
        ("media as object not a list", {"media": {"link": {"reference": "Media/1"}}}),
        ("media link as string", {"media": [{"link": "Media/1"}]}),
        ("conclusion as number", {"conclusion": 5}),
        ("conclusionCode as object not a list", {"conclusionCode": {"text": "x"}}),
        ("presentedForm as object not a list", {"presentedForm": {"title": "x"}}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "DiagnosticReport",
        "id": "110001",
        "status": "final",
        "code": CODE,
        "subject": SUBJECT,
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), report_pb2.DiagnosticReport, validate=True
        )

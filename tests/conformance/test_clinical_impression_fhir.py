"""FHIR R4 conformance for `to_fhir_clinical_impression()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

ClinicalImpression is stored Medplum-style (like Patient, Appointment, Encounter, Condition,
Procedure, DiagnosticReport, Immunization, RiskAssessment and the other content-based
resources): the resource lives whole in ClinicalImpressionModel.content, and
to_fhir_clinical_impression() only stamps `id` and `meta` onto it. So what can go wrong on the
read side is that stamping (e.g. a malformed meta extension) or a stored document the server
returns that isn't valid R4 — each case below is a `content` document as the write path would
store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.clinical_impression import to_fhir_clinical_impression
from app.models.clinical_impression import ClinicalImpressionModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.clinical_impression_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
SUBJECT = {"reference": "Patient/10001"}
SCT = "http://snomed.info/sct"
BASE = {"status": "completed", "subject": SUBJECT}


def _impression(content: dict, **overrides) -> ClinicalImpressionModel:
    fields = {
        "clinical_impression_id": 530001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return ClinicalImpressionModel(**fields)


def _with(**elements) -> ClinicalImpressionModel:
    return _impression({**BASE, **elements})


CASES = {
    "minimal": _with(),
    "updated_by_and_updated_at": _impression(dict(BASE), updated_by="u-other", updated_at=D),
    "identifier_with_type_and_assigner": _with(
        identifier=[
            {
                "use": "official",
                "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "FILL"}]},
                "system": "https://fhir-server.dev/fhir/identifier-system/clinical-impression-id",
                "value": "CI-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    **{f"status_{s}": _impression({"status": s, "subject": SUBJECT}) for s in ("in-progress", "completed", "entered-in-error")},
    "status_reason_and_code": _with(
        statusReason={"text": "Superseded"},
        code={"coding": [{"system": SCT, "code": "225338004"}], "text": "Assessment"},
    ),
    "description_and_summary": _with(description="Why and how.", summary="Stable angina suspected."),
    **{
        f"subject_{t}": _impression({"status": "completed", "subject": {"reference": f"{t}/1"}})
        for t in ("Patient", "Group")
    },
    "subject_with_display": _with(subject={"reference": "Patient/10001", "display": "A. Patient"}),
    "subject_logical": _with(subject={"identifier": {"system": "urn:pts", "value": "P-9"}}),
    "subject_absolute_url": _with(subject={"reference": "https://other.example.org/fhir/Patient/9"}),
    "encounter": _with(encounter={"reference": "Encounter/20001"}),
    "effective_date_time": _with(effectiveDateTime="2023-01-15T09:30:00Z"),
    "effective_date_time_partial": _with(effectiveDateTime="2023-01"),
    "effective_period": _with(effectivePeriod={"start": "2023-01-01", "end": "2023-06-01"}),
    "date": _with(date="2023-01-15T10:00:00Z"),
    "date_partial": _with(date="2023"),
    **{f"assessor_{t}": _with(assessor={"reference": f"{t}/1"}) for t in ("Practitioner", "PractitionerRole")},
    "assessor_logical": _with(assessor={"identifier": {"system": "urn:who", "value": "W-1"}}),
    "previous": _with(previous={"reference": "ClinicalImpression/530001"}),
    **{f"problem_{t}": _with(problem=[{"reference": f"{t}/1"}]) for t in ("Condition", "AllergyIntolerance")},
    "problems": _with(problem=[{"reference": "Condition/1"}, {"reference": "AllergyIntolerance/2"}]),
    "investigation_minimal": _with(investigation=[{"code": {"text": "Labs"}}]),
    **{
        f"investigation_item_{t}": _with(
            investigation=[{"code": {"text": "Set"}, "item": [{"reference": f"{t}/1"}]}]
        )
        for t in ("Observation", "QuestionnaireResponse", "FamilyMemberHistory", "DiagnosticReport", "RiskAssessment",
                  "ImagingStudy", "Media")
    },
    "investigation_several": _with(
        investigation=[
            {"code": {"coding": [{"system": SCT, "code": "225338004"}]}, "item": [{"reference": "Observation/1"}]},
            {"code": {"text": "Follow-up"}},
        ]
    ),
    "protocol": _with(protocol=["http://example.org/protocols/a", "http://example.org/protocols/b"]),
    "finding_empty": _with(finding=[{}]),
    "finding_item_codeable_concept": _with(
        finding=[{"itemCodeableConcept": {"coding": [{"system": SCT, "code": "194828000", "display": "Angina"}]}}]
    ),
    **{
        f"finding_item_reference_{t}": _with(finding=[{"itemReference": {"reference": f"{t}/1"}}])
        for t in ("Condition", "Observation", "Media")
    },
    "finding_basis": _with(finding=[{"itemCodeableConcept": {"text": "Fever"}, "basis": "Temperature chart."}]),
    "prognosis_codeable_concept": _with(
        prognosisCodeableConcept=[{"coding": [{"system": SCT, "code": "170968001"}]}, {"text": "Good"}]
    ),
    "prognosis_reference": _with(prognosisReference=[{"reference": "RiskAssessment/520001"}]),
    "supporting_info": _with(
        supportingInfo=[{"reference": "Observation/160001"}, {"reference": "Condition/120001"},
                        {"reference": "Questionnaire/380001"}]
    ),
    "note_author_string": _with(note=[{"text": "Review in 2 weeks.", "time": "2023-01-15T10:00:00Z", "authorString": "Nurse Joy"}]),
    "note_author_reference": _with(note=[{"text": "n", "authorReference": {"reference": "Practitioner/30001"}}]),
    "extension": _with(extension=[{"url": "https://fhir-server.dev/fhir/StructureDefinition/x", "valueString": "y"}]),
    "full": _with(
        identifier=[{"system": "urn:ci", "value": "CI-1"}],
        statusReason={"text": "Done"},
        code={"text": "Assessment"},
        description="Assessment of chest pain.",
        encounter={"reference": "Encounter/20001"},
        effectiveDateTime="2023-01-15T09:30:00Z",
        date="2023-01-15T10:00:00Z",
        assessor={"reference": "Practitioner/30001"},
        previous={"reference": "ClinicalImpression/530000"},
        problem=[{"reference": "Condition/120001"}],
        investigation=[{"code": {"text": "Labs"}, "item": [{"reference": "DiagnosticReport/110001"}]}],
        protocol=["http://example.org/protocols/a"],
        summary="Stable angina suspected.",
        finding=[{"itemCodeableConcept": {"text": "Angina"}, "itemReference": {"reference": "Condition/120001"},
                  "basis": "ECG"}],
        prognosisCodeableConcept=[{"text": "Good"}],
        prognosisReference=[{"reference": "RiskAssessment/520001"}],
        supportingInfo=[{"reference": "Observation/160001"}],
        note=[{"text": "n"}],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_clinical_impression_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.ClinicalImpression, to_fhir_clinical_impression(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {**BASE, "summary": "Stable angina suspected.", "finding": [{"basis": "ECG"}]}
    out = to_fhir_clinical_impression(_impression(content))
    assert out["resourceType"] == "ClinicalImpression"
    assert out["id"] == "530001"
    assert {k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")} == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — `subject`, `code` or `assessor` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("subject as string not a Reference", {"subject": "Patient/1"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("code as string not a CodeableConcept", {"code": "x"}),
        ("statusReason as string not a CodeableConcept", {"statusReason": "x"}),
        ("date not a dateTime", {"date": "yesterday"}),
        ("effectiveDateTime not a dateTime", {"effectiveDateTime": "yesterday"}),
        ("effectivePeriod as string", {"effectivePeriod": "2023"}),
        ("encounter as string not a Reference", {"encounter": "Encounter/1"}),
        ("assessor as string not a Reference", {"assessor": "Practitioner/1"}),
        ("previous as string not a Reference", {"previous": "ClinicalImpression/1"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("problem as object not a list", {"problem": {"reference": "Condition/1"}}),
        ("investigation as object not a list", {"investigation": {"code": {"text": "x"}}}),
        ("investigation code as string", {"investigation": [{"code": "x"}]}),
        ("investigation item as object not a list", {"investigation": [{"code": {"text": "x"}, "item": {"reference": "Observation/1"}}]}),
        ("protocol as string not a list", {"protocol": "http://example.org/p"}),
        ("summary as number", {"summary": 5}),
        ("finding as object not a list", {"finding": {"basis": "x"}}),
        ("finding itemCodeableConcept as string", {"finding": [{"itemCodeableConcept": "x"}]}),
        ("finding itemReference as string", {"finding": [{"itemReference": "Condition/1"}]}),
        ("finding basis as number", {"finding": [{"basis": 5}]}),
        ("prognosisCodeableConcept as string", {"prognosisCodeableConcept": "good"}),
        ("prognosisReference as object not a list", {"prognosisReference": {"reference": "RiskAssessment/1"}}),
        ("supportingInfo as object not a list", {"supportingInfo": {"reference": "Observation/1"}}),
        ("note as object not a list", {"note": {"text": "x"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "ClinicalImpression", "id": "530001", **BASE, **broken}
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(fhir_json_text(payload), pb2.ClinicalImpression, validate=True)

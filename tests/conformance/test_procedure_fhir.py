"""FHIR R4 conformance for `to_fhir_procedure()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Procedure is stored Medplum-style (like Patient, Appointment, Encounter, Condition
and the other content-based resources): the resource lives whole in
ProcedureModel.content, and to_fhir_procedure() only stamps `id` and `meta` onto
it. So what can go wrong on the read side is that stamping (e.g. a malformed meta
extension) or a stored document the server returns that isn't valid R4 — each case
below is a `content` document as the write path would store it, run through the
real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.procedure import to_fhir_procedure
from app.models.procedure import ProcedureModel

from .support import assert_valid, fhir_json_text

procedure_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.procedure_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
SUBJECT = {"reference": "Patient/10001"}
SCT = "http://snomed.info/sct"


def _procedure(content: dict, **overrides) -> ProcedureModel:
    fields = {
        "procedure_id": 100001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return ProcedureModel(**fields)


def _with(**elements) -> ProcedureModel:
    return _procedure({"status": "completed", "subject": SUBJECT, **elements})


_AGE = {
    "value": 12,
    "unit": "years",
    "system": "http://unitsofmeasure.org",
    "code": "a",
}
_RANGE = {"low": {"value": 5, "unit": "years"}, "high": {"value": 10, "unit": "years"}}

CASES = {
    "minimal": _with(),
    "updated_by_and_updated_at": _procedure(
        {"status": "completed", "subject": SUBJECT}, updated_by="u-other", updated_at=D
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
                "system": "https://fhir-server.dev/fhir/identifier-system/procedure-id",
                "value": "PR-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    **{
        f"status_{s}": _procedure({"status": s, "subject": SUBJECT})
        for s in (
            "preparation",
            "in-progress",
            "not-done",
            "on-hold",
            "stopped",
            "completed",
            "entered-in-error",
            "unknown",
        )
    },
    "instantiates": _with(
        instantiatesCanonical=["http://example.org/fhir/PlanDefinition/pd1|1.0"],
        instantiatesUri=["http://example.org/protocols/knee"],
    ),
    "based_on": _with(
        basedOn=[
            {"reference": "ServiceRequest/80001"},
            {"reference": "CarePlan/290001"},
        ]
    ),
    "part_of": _with(
        partOf=[{"reference": "Procedure/100002"}, {"reference": "Observation/160001"}]
    ),
    "status_reason": _with(
        statusReason={"coding": [{"system": SCT, "code": "416406003"}]},
        status="not-done",
    ),
    "category": _with(
        category={
            "coding": [{"system": SCT, "code": "387713003", "display": "Surgical"}],
            "text": "Surgery",
        }
    ),
    "code": _with(
        code={
            "coding": [{"system": SCT, "code": "80146002", "display": "Appendectomy"}],
            "text": "Appendix removal",
        }
    ),
    "subject_with_display": _with(
        subject={"reference": "Patient/10001", "display": "A. Patient"}
    ),
    "subject_group": _procedure(
        {"status": "completed", "subject": {"reference": "Group/5"}}
    ),
    "subject_logical": _procedure(
        {
            "status": "completed",
            "subject": {"identifier": {"system": "urn:pts", "value": "P-9"}},
        }
    ),
    "subject_absolute_url": _procedure(
        {
            "status": "completed",
            "subject": {"reference": "https://other.example.org/fhir/Patient/9"},
        }
    ),
    "encounter": _with(encounter={"reference": "Encounter/20001"}),
    "performed_date_time": _with(performedDateTime="2023-01-15T09:30:00Z"),
    "performed_date_time_partial": _with(performedDateTime="2023-01"),
    "performed_period": _with(
        performedPeriod={"start": "2020-01-01", "end": "2020-02-01"}
    ),
    "performed_period_open": _with(performedPeriod={"start": "2020-01-01"}),
    "performed_string": _with(performedString="as a child"),
    "performed_age": _with(performedAge=_AGE),
    "performed_range": _with(performedRange=_RANGE),
    **{
        f"recorder_{t}": _with(recorder={"reference": f"{t}/1"})
        for t in ("Practitioner", "PractitionerRole", "Patient", "RelatedPerson")
    },
    **{
        f"asserter_{t}": _with(asserter={"reference": f"{t}/1"})
        for t in ("Practitioner", "PractitionerRole", "Patient", "RelatedPerson")
    },
    **{
        f"performer_{t}": _with(performer=[{"actor": {"reference": f"{t}/1"}}])
        for t in (
            "Practitioner",
            "PractitionerRole",
            "Organization",
            "Patient",
            "RelatedPerson",
            "Device",
        )
    },
    "performer_full": _with(
        performer=[
            {
                "function": {"coding": [{"system": SCT, "code": "304292004"}]},
                "actor": {"reference": "Practitioner/30001"},
                "onBehalfOf": {"reference": "Organization/190001"},
            }
        ]
    ),
    "performer_logical": _with(
        performer=[{"actor": {"identifier": {"system": "urn:who", "value": "W-1"}}}]
    ),
    "location": _with(location={"reference": "Location/230001"}),
    "reason_code": _with(
        reasonCode=[
            {"coding": [{"system": SCT, "code": "74400008"}]},
            {"text": "Sports injury"},
        ]
    ),
    "reason_reference": _with(
        reasonReference=[
            {"reference": "Condition/120001"},
            {"reference": "Observation/160001"},
            {"reference": "Procedure/100002"},
            {"reference": "DiagnosticReport/110001"},
            {"reference": "DocumentReference/320001"},
        ]
    ),
    "body_site": _with(
        bodySite=[
            {"coding": [{"system": SCT, "code": "66754008"}]},
            {"text": "Left knee"},
        ]
    ),
    "outcome": _with(
        outcome={"coding": [{"system": SCT, "code": "385669000"}], "text": "Successful"}
    ),
    "report": _with(
        report=[
            {"reference": "DiagnosticReport/110001"},
            {"reference": "Composition/1"},
        ]
    ),
    "complication": _with(
        complication=[{"coding": [{"system": SCT, "code": "131148009"}]}]
    ),
    "complication_detail": _with(
        complicationDetail=[{"reference": "Condition/120001"}]
    ),
    "follow_up": _with(followUp=[{"text": "Review in two weeks"}]),
    "note_author_reference": _with(
        note=[
            {
                "authorReference": {"reference": "Practitioner/30001"},
                "time": "2023-01-15T11:00:00Z",
                "text": "Uneventful",
            }
        ]
    ),
    "note_author_string": _with(
        note=[{"authorString": "Dr Smith", "text": "Uneventful"}]
    ),
    "focal_device": _with(
        focalDevice=[
            {
                "action": {"coding": [{"system": SCT, "code": "129338003"}]},
                "manipulated": {"reference": "Device/7"},
            }
        ]
    ),
    "used": _with(
        usedReference=[{"reference": "Device/7"}, {"reference": "Medication/250001"}],
        usedCode=[{"coding": [{"system": SCT, "code": "86174004"}]}],
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
        identifier=[{"system": "urn:pr", "value": "PR-1"}],
        instantiatesUri=["http://example.org/protocols/knee"],
        category={"coding": [{"system": SCT, "code": "387713003"}]},
        code={"coding": [{"system": SCT, "code": "80146002"}]},
        encounter={"reference": "Encounter/20001"},
        performedPeriod={
            "start": "2023-01-15T09:30:00Z",
            "end": "2023-01-15T10:45:00Z",
        },
        recorder={"reference": "Practitioner/30001"},
        asserter={"reference": "Practitioner/30001"},
        performer=[{"actor": {"reference": "Practitioner/30001"}}],
        location={"reference": "Location/230001"},
        reasonCode=[{"coding": [{"system": SCT, "code": "74400008"}]}],
        reasonReference=[{"reference": "Condition/120001"}],
        bodySite=[{"coding": [{"system": SCT, "code": "66754008"}]}],
        outcome={"coding": [{"system": SCT, "code": "385669000"}]},
        note=[{"text": "Uneventful"}],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_procedure_mapper_emits_valid_fhir_r4(case):
    assert_valid(procedure_pb2.Procedure, to_fhir_procedure(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {"status": "completed", "subject": SUBJECT, "performedDateTime": "2023"}
    out = to_fhir_procedure(_procedure(content))
    assert out["resourceType"] == "Procedure"
    assert out["id"] == "100001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — `subject` or `category` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("subject as string not a Reference", {"subject": "Patient/1"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("code as string not a CodeableConcept", {"code": "80146002"}),
        ("performedDateTime not a dateTime", {"performedDateTime": "yesterday"}),
        ("performedAge value as string", {"performedAge": {"value": "twelve"}}),
        ("performedString as number", {"performedString": 5}),
        (
            "performer as object not a list",
            {"performer": {"actor": {"reference": "Practitioner/1"}}},
        ),
        ("performer actor as string", {"performer": [{"actor": "Practitioner/1"}]}),
        ("reasonCode as object not a list", {"reasonCode": {"text": "x"}}),
        (
            "reasonReference as object not a list",
            {"reasonReference": {"reference": "Condition/1"}},
        ),
        ("instantiatesUri as string not a list", {"instantiatesUri": "http://x"}),
        ("bodySite as object not a list", {"bodySite": {"text": "x"}}),
        ("note as object not a list", {"note": {"text": "x"}}),
        (
            "focalDevice as object not a list",
            {"focalDevice": {"manipulated": {"reference": "Device/1"}}},
        ),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "Procedure",
        "id": "100001",
        "status": "completed",
        "subject": SUBJECT,
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), procedure_pb2.Procedure, validate=True
        )

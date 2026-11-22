"""FHIR R4 conformance for `to_fhir_care_plan()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

CarePlan is stored Medplum-style (like Patient, Appointment, Encounter, Condition, ServiceRequest,
CareTeam, Group and the other content-based resources): the resource lives whole in
CarePlanModel.content, and to_fhir_care_plan() only stamps `id` and `meta` onto it. So what can go
wrong on the read side is that stamping (e.g. a malformed meta extension) or a stored document
the server returns that isn't valid R4 - each case below is a `content` document as the write path
would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.care_plan import to_fhir_care_plan
from app.models.care_plan import CarePlanModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.care_plan_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
SCT = "http://snomed.info/sct"
BASE = {"status": "active", "intent": "plan", "subject": {"reference": "Patient/10001"}}
CODE = {"coding": [{"system": SCT, "code": "386053000", "display": "Evaluation"}]}


def _c(content: dict, **overrides) -> CarePlanModel:
    fields = {
        "care_plan_id": 290001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return CarePlanModel(**fields)


def _with(**extra) -> CarePlanModel:
    return _c({**BASE, **extra})


def _detail(**extra):
    return {"activity": [{"detail": {"status": "scheduled", **extra}}]}


CASES = {
    "minimal": _c(BASE),
    "updated_by_and_updated_at": _c(BASE, updated_by="u-other", updated_at=D),
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
                "system": "https://fhir-server.dev/fhir/identifier-system/care-plan-id",
                "value": "CP-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    **{
        f"status_{s}": _c({**BASE, "status": s})
        for s in (
            "draft",
            "active",
            "on-hold",
            "revoked",
            "completed",
            "entered-in-error",
            "unknown",
        )
    },
    **{
        f"intent_{i}": _c({**BASE, "intent": i})
        for i in ("proposal", "plan", "order", "option")
    },
    "instantiates": _with(
        instantiatesCanonical=["http://example.org/fhir/PlanDefinition/p|1.0"],
        instantiatesUri=["http://example.org/protocols/p"],
    ),
    "based_on_replaces_part_of": _with(
        basedOn=[{"reference": "CarePlan/290002"}],
        replaces=[{"reference": "CarePlan/290003"}],
        partOf=[{"reference": "CarePlan/290004"}],
    ),
    "category_coded_and_text": _with(
        category=[CODE, {"text": "Home care"}],
    ),
    "title_description_created": _with(
        title="Diabetes plan",
        description="Manage diabetes",
        created="2026-01-01T09:00:00Z",
    ),
    "subject_group": _c({**BASE, "subject": {"reference": "Group/430001"}}),
    "subject_logical": _c(
        {**BASE, "subject": {"identifier": {"system": "urn:s", "value": "S-9"}}}
    ),
    "subject_absolute_url": _c(
        {**BASE, "subject": {"reference": "https://other.example.org/fhir/Patient/1"}}
    ),
    "encounter": _with(encounter={"reference": "Encounter/20001"}),
    "period_closed": _with(period={"start": "2026-01-01", "end": "2026-06-30"}),
    "period_open_ended": _with(period={"start": "2026-01-01T09:00:00Z"}),
    **{
        f"author_{t}": _with(author={"reference": f"{t}/1"})
        for t in (
            "Patient",
            "Practitioner",
            "PractitionerRole",
            "Device",
            "RelatedPerson",
            "Organization",
            "CareTeam",
        )
    },
    "contributor": _with(
        contributor=[
            {"reference": "Practitioner/30001"},
            {"reference": "Organization/190001"},
        ]
    ),
    "care_team_addresses_goal": _with(
        careTeam=[{"reference": "CareTeam/390001"}],
        addresses=[{"reference": "Condition/120001"}],
        goal=[{"reference": "Goal/460001"}],
    ),
    "supporting_info_any": _with(
        supportingInfo=[
            {"reference": "Observation/160001"},
            {"reference": "DocumentReference/1"},
        ]
    ),
    "activity_reference": _with(
        activity=[{"reference": {"reference": "ServiceRequest/80001"}}]
    ),
    **{
        f"activity_reference_{t}": _with(
            activity=[{"reference": {"reference": f"{t}/1"}}]
        )
        for t in (
            "Appointment",
            "CommunicationRequest",
            "DeviceRequest",
            "MedicationRequest",
            "NutritionOrder",
            "Task",
            "ServiceRequest",
            "VisionPrescription",
            "RequestGroup",
        )
    },
    "activity_outcome_and_progress": _with(
        activity=[
            {
                "outcomeCodeableConcept": [CODE],
                "outcomeReference": [{"reference": "Observation/160001"}],
                "progress": [
                    {"text": "On track", "time": "2026-03-01T10:00:00Z"},
                    {"authorString": "Dr A", "text": "Second"},
                ],
                "reference": {"reference": "Appointment/40001"},
            }
        ]
    ),
    **{
        f"activity_detail_kind_{k}": _with(**_detail(kind=k))
        for k in (
            "Appointment",
            "CommunicationRequest",
            "DeviceRequest",
            "MedicationRequest",
            "NutritionOrder",
            "Task",
            "ServiceRequest",
            "VisionPrescription",
        )
    },
    **{
        f"activity_detail_status_{s}": _with(activity=[{"detail": {"status": s}}])
        for s in (
            "not-started",
            "scheduled",
            "in-progress",
            "on-hold",
            "completed",
            "cancelled",
            "stopped",
            "unknown",
            "entered-in-error",
        )
    },
    "activity_detail_code_and_reasons": _with(
        **_detail(
            code=CODE,
            reasonCode=[CODE],
            reasonReference=[
                {"reference": "Condition/120001"},
                {"reference": "Observation/160001"},
            ],
            goal=[{"reference": "Goal/460001"}],
            statusReason={"text": "Started"},
            doNotPerform=False,
        )
    ),
    "activity_detail_scheduled_period": _with(
        **_detail(scheduledPeriod={"start": "2026-02-01", "end": "2026-02-28"})
    ),
    "activity_detail_scheduled_timing": _with(
        **_detail(
            scheduledTiming={
                "event": ["2026-05-01T08:00:00Z"],
                "repeat": {"frequency": 1, "period": 1, "periodUnit": "d"},
            }
        )
    ),
    "activity_detail_scheduled_string": _with(**_detail(scheduledString="next week")),
    "activity_detail_location_performers": _with(
        **_detail(
            location={"reference": "Location/230001"},
            performer=[
                {"reference": "Practitioner/30001"},
                {"reference": "CareTeam/390001"},
                {"reference": "Device/5"},
            ],
        )
    ),
    "activity_detail_product_codeable_concept": _with(
        **_detail(productCodeableConcept=CODE)
    ),
    "activity_detail_product_reference": _with(
        **_detail(productReference={"reference": "Medication/250001"})
    ),
    "activity_detail_quantities": _with(
        **_detail(
            dailyAmount={
                "value": 2,
                "unit": "mg",
                "system": "http://unitsofmeasure.org",
                "code": "mg",
            },
            quantity={"value": 10, "unit": "mg"},
            description="Daily walk",
            instantiatesCanonical=["http://example.org/fhir/ActivityDefinition/a"],
            instantiatesUri=["http://example.org/a"],
        )
    ),
    "activities_several": _with(
        activity=[
            {"reference": {"reference": "ServiceRequest/80001"}},
            {"detail": {"status": "completed"}},
            {"progress": [{"text": "x"}]},
        ]
    ),
    "note_author_reference": _with(
        note=[
            {
                "authorReference": {"reference": "Practitioner/30001"},
                "time": "2026-02-01T10:00:00Z",
                "text": "Review monthly.",
            }
        ]
    ),
    "note_author_string": _with(note=[{"authorString": "Dr. A", "text": "x"}]),
    "extension": _with(extension=[{"url": "https://x/ext", "valueString": "y"}]),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_care_plan_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.CarePlan, to_fhir_care_plan(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {**BASE, "title": "Diabetes plan"}
    out = to_fhir_care_plan(_c(content))
    assert out["resourceType"] == "CarePlan"
    assert out["id"] == "290001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `subject` or `period` as a one-item list; the integration
# tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "retired"}),
        ("status as number", {"status": 1}),
        ("intent with an unknown code", {"intent": "directive"}),
        ("title as number", {"title": 5}),
        ("category as object not a list", {"category": {"text": "x"}}),
        ("category entry as string", {"category": ["x"]}),
        ("subject as string", {"subject": "Patient/1"}),
        ("encounter as string", {"encounter": "Encounter/1"}),
        ("period as string", {"period": "2026"}),
        ("period start as number", {"period": {"start": 2026}}),
        ("created as number", {"created": 5}),
        ("author as string", {"author": "Practitioner/1"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("basedOn as object not a list", {"basedOn": {"reference": "CarePlan/1"}}),
        ("instantiatesCanonical as string", {"instantiatesCanonical": "http://x"}),
        ("instantiatesUri as string", {"instantiatesUri": "http://x"}),
        ("careTeam as object", {"careTeam": {"reference": "CareTeam/1"}}),
        ("addresses as object", {"addresses": {"reference": "Condition/1"}}),
        ("goal as object", {"goal": {"reference": "Goal/1"}}),
        (
            "activity as object not a list",
            {"activity": {"detail": {"status": "scheduled"}}},
        ),
        (
            "activity reference as string",
            {"activity": [{"reference": "Appointment/1"}]},
        ),
        (
            "activity detail status with an unknown code",
            {"activity": [{"detail": {"status": "done"}}]},
        ),
        (
            "activity detail without status",
            {"activity": [{"detail": {"description": "x"}}]},
        ),
        (
            "activity detail kind with an unknown code",
            {"activity": [{"detail": {"status": "scheduled", "kind": "Observation"}}]},
        ),
        (
            "activity detail doNotPerform as string",
            {"activity": [{"detail": {"status": "scheduled", "doNotPerform": "no"}}]},
        ),
        (
            "activity detail scheduledPeriod as string",
            {
                "activity": [
                    {"detail": {"status": "scheduled", "scheduledPeriod": "2026"}}
                ]
            },
        ),
        (
            "activity detail performer as object",
            {
                "activity": [
                    {
                        "detail": {
                            "status": "scheduled",
                            "performer": {"reference": "Practitioner/1"},
                        }
                    }
                ]
            },
        ),
        (
            "activity detail location as string",
            {
                "activity": [
                    {"detail": {"status": "scheduled", "location": "Location/1"}}
                ]
            },
        ),
        ("note as object not a list", {"note": {"text": "x"}}),
        ("note without text", {"note": [{"authorString": "x"}]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "CarePlan", "id": "290001", **BASE, **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.CarePlan, validate=True
        )

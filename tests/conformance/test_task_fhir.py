"""FHIR R4 conformance for `to_fhir_task()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Task is stored content-based (like Goal, CarePlan, Patient and the other rebuilt resources): the
resource lives whole in TaskModel.content, and to_fhir_task() only stamps `id` and `meta` onto
it. So what can go wrong on the read side is that stamping (e.g. a malformed meta extension) or a
stored document the server returns that isn't valid R4 - each case below is a `content` document
as the write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.task import to_fhir_task
from app.models.task import TaskModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.task_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
SCT = "http://snomed.info/sct"
BASE = {"status": "requested", "intent": "order"}


def _task(content: dict, **overrides) -> TaskModel:
    fields = {
        "task_id": 280001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return TaskModel(**fields)


def _t(**extra) -> TaskModel:
    return _task({**BASE, **extra})


CASES = {
    "minimal": _task(BASE),
    "updated_by_and_updated_at": _task(BASE, updated_by="u-other", updated_at=D),
    **{
        f"status_{s}": _t(status=s)
        for s in (
            "draft",
            "requested",
            "received",
            "accepted",
            "rejected",
            "ready",
            "cancelled",
            "in-progress",
            "on-hold",
            "failed",
            "completed",
            "entered-in-error",
        )
    },
    **{
        f"intent_{i}": _t(intent=i)
        for i in (
            "unknown",
            "proposal",
            "plan",
            "order",
            "original-order",
            "reflex-order",
            "filler-order",
            "instance-order",
            "option",
        )
    },
    **{f"priority_{p}": _t(priority=p) for p in ("routine", "urgent", "asap", "stat")},
    "identifier_with_type_and_assigner": _t(
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
                "system": "https://fhir-server.dev/fhir/identifier-system/task-id",
                "value": "T-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "instantiates": _t(
        instantiatesCanonical="http://example.org/ActivityDefinition/x|1.0",
        instantiatesUri="http://example.org/protocols/x",
    ),
    "based_on_any_type": _t(
        basedOn=[
            {"reference": "ServiceRequest/80001"},
            {"reference": "Device/7"},
            {"reference": "https://other.example.org/fhir/CarePlan/9"},
        ]
    ),
    "group_identifier": _t(groupIdentifier={"system": "urn:g", "value": "GRP-1"}),
    "part_of": _t(partOf=[{"reference": "Task/280000"}]),
    "status_reason_and_business_status": _t(
        statusReason={"text": "waiting for the lab"},
        businessStatus={"coding": [{"system": SCT, "code": "1"}], "text": "Waiting"},
    ),
    "code": _t(code={"coding": [{"system": SCT, "code": "2", "display": "Fulfill"}]}),
    "description": _t(description="Collect a blood sample"),
    "focus_and_for": _t(
        focus={"reference": "ServiceRequest/80001"},
        **{"for": {"reference": "Patient/10001"}},
    ),
    "for_group": _t(**{"for": {"reference": "Group/430001"}}),
    "for_logical": _t(
        **{"for": {"identifier": {"system": "urn:mrn", "value": "M-9"}, "display": "J"}}
    ),
    "encounter": _t(encounter={"reference": "Encounter/20001"}),
    "execution_period": _t(
        executionPeriod={"start": "2026-02-01T09:00:00Z", "end": "2026-02-01T10:00:00Z"}
    ),
    "authored_and_modified": _t(
        authoredOn="2026-01-15T08:00:00Z", lastModified="2026-01-16T09:00:00Z"
    ),
    "requester_owner_location": _t(
        requester={"reference": "Practitioner/30001"},
        owner={"reference": "Organization/190001"},
        location={"reference": "Location/230001"},
    ),
    "performer_type": _t(performerType=[{"text": "requester"}, {"text": "scheduler"}]),
    "reason": _t(
        reasonCode={"text": "routine"},
        reasonReference={"reference": "Condition/120001"},
    ),
    "insurance_note_history": _t(
        insurance=[{"reference": "Coverage/9"}],
        note=[
            {"text": "Fasting", "time": "2026-01-15T08:00:00Z"},
            {
                "text": "By a person",
                "authorReference": {"reference": "Practitioner/30001"},
            },
        ],
        relevantHistory=[{"reference": "Provenance/9"}],
    ),
    "restriction": _t(
        restriction={
            "repetitions": 2,
            "period": {"end": "2026-02-15T00:00:00Z"},
            "recipient": [
                {"reference": "Patient/10001"},
                {"reference": "Group/430001"},
            ],
        }
    ),
    "input_output_value_choices": _t(
        input=[
            {"type": {"text": "a"}, "valueString": "x"},
            {"type": {"text": "b"}, "valueBoolean": True},
            {"type": {"text": "c"}, "valueInteger": 5},
            {"type": {"text": "d"}, "valueDecimal": 1.5},
            {"type": {"text": "e"}, "valueDateTime": "2026-01-15T08:00:00Z"},
            {"type": {"text": "f"}, "valueQuantity": {"value": 5, "unit": "mL"}},
            {"type": {"text": "g"}, "valueCodeableConcept": {"text": "x"}},
            {"type": {"text": "h"}, "valueReference": {"reference": "Patient/10001"}},
            {"type": {"text": "i"}, "valueCoding": {"system": SCT, "code": "3"}},
            {"type": {"text": "j"}, "valuePeriod": {"start": "2026-01-01"}},
        ],
        output=[
            {"type": {"text": "k"}, "valueString": "done"},
            {"type": {"text": "l"}, "valueUri": "http://example.org/r"},
        ],
    ),
    "extension": _t(
        extension=[
            {
                "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                "valueString": "y",
            }
        ]
    ),
    "full": _t(
        identifier=[{"system": "urn:t", "value": "T-1"}],
        priority="urgent",
        code={"text": "fulfill"},
        description="d",
        focus={"reference": "ServiceRequest/80001"},
        encounter={"reference": "Encounter/20001"},
        authoredOn="2026-01-15T08:00:00Z",
        requester={"reference": "Practitioner/30001"},
        owner={"reference": "Practitioner/30001"},
        input=[{"type": {"text": "a"}, "valueString": "x"}],
        **{"for": {"reference": "Patient/10001"}},
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_task_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.Task, to_fhir_task(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {
        **BASE,
        "description": "Collect",
        "for": {"reference": "Patient/10001"},
    }
    out = to_fhir_task(_task(content))
    assert out["resourceType"] == "Task"
    assert out["id"] == "280001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `code`, `for` or `restriction` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("intent with an unknown code", {"intent": "robot"}),
        ("priority with an unknown code", {"priority": "now"}),
        ("code as string not a CodeableConcept", {"code": "x"}),
        ("businessStatus as string", {"businessStatus": "x"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("groupIdentifier as string", {"groupIdentifier": "x"}),
        (
            "basedOn as object not a list",
            {"basedOn": {"reference": "ServiceRequest/1"}},
        ),
        ("partOf as object not a list", {"partOf": {"reference": "Task/1"}}),
        ("focus as string not a Reference", {"focus": "ServiceRequest/1"}),
        ("for as string not a Reference", {"for": "Patient/1"}),
        ("encounter as string", {"encounter": "Encounter/1"}),
        ("executionPeriod as string", {"executionPeriod": "today"}),
        ("authoredOn not a dateTime", {"authoredOn": "yesterday"}),
        ("lastModified as number", {"lastModified": 5}),
        ("requester as string", {"requester": "Practitioner/1"}),
        ("owner as string", {"owner": "Practitioner/1"}),
        ("performerType as object not a list", {"performerType": {"text": "x"}}),
        ("description as number", {"description": 5}),
        ("note as string", {"note": "x"}),
        ("restriction as string", {"restriction": "x"}),
        (
            "restriction repetitions as string",
            {"restriction": {"repetitions": "twice"}},
        ),
        ("input as object not a list", {"input": {"type": {"text": "x"}}}),
        (
            "input valueBoolean as string",
            {"input": [{"type": {"text": "x"}, "valueBoolean": "yes"}]},
        ),
        ("output type as string", {"output": [{"type": "x", "valueString": "y"}]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Task", "id": "280001", **BASE, **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.Task, validate=True
        )

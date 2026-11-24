"""FHIR R4 conformance for `to_fhir_goal()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Goal is stored content-based (like CarePlan, CareTeam, Patient and the other rebuilt resources):
the resource lives whole in GoalModel.content, and to_fhir_goal() only stamps `id` and `meta`
onto it. So what can go wrong on the read side is that stamping (e.g. a malformed meta
extension) or a stored document the server returns that isn't valid R4 - each case below is a
`content` document as the write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.goal import to_fhir_goal
from app.models.goal import GoalModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.goal_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
SCT = "http://snomed.info/sct"
LOINC = "http://loinc.org"
DESCRIPTION = {"text": "Reduce HbA1c below 7%"}
SUBJECT = {"reference": "Patient/10001"}
BASE = {"lifecycleStatus": "active", "description": DESCRIPTION, "subject": SUBJECT}


def _goal(content: dict, **overrides) -> GoalModel:
    fields = {
        "goal_id": 460001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return GoalModel(**fields)


def _g(**extra) -> GoalModel:
    return _goal({**BASE, **extra})


CASES = {
    "minimal": _goal(BASE),
    "updated_by_and_updated_at": _goal(BASE, updated_by="u-other", updated_at=D),
    **{
        f"status_{s}": _g(lifecycleStatus=s)
        for s in (
            "proposed",
            "planned",
            "accepted",
            "active",
            "on-hold",
            "completed",
            "cancelled",
            "entered-in-error",
            "rejected",
        )
    },
    "identifier_with_type_and_assigner": _g(
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
                "system": "https://fhir-server.dev/fhir/identifier-system/goal-id",
                "value": "G-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "achievement_status": _g(
        achievementStatus={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/goal-achievement",
                    "code": "achieved",
                }
            ]
        }
    ),
    "achievement_status_text_only": _g(achievementStatus={"text": "Stalled"}),
    "category": _g(
        category=[{"text": "dietary"}, {"coding": [{"system": SCT, "code": "1"}]}]
    ),
    "priority": _g(
        priority={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/goal-priority",
                    "code": "high-priority",
                }
            ]
        }
    ),
    "description_coded": _g(
        description={
            "coding": [{"system": SCT, "code": "73211009", "display": "Diabetes"}]
        }
    ),
    "subject_group": _g(subject={"reference": "Group/430001"}),
    "subject_organization": _g(subject={"reference": "Organization/190001"}),
    "subject_logical": _g(
        subject={"identifier": {"system": "urn:mrn", "value": "M-9"}, "display": "Jane"}
    ),
    "subject_absolute_url": _g(
        subject={"reference": "https://other.example.org/fhir/Patient/1"}
    ),
    "start_date": _g(startDate="2026-01-15"),
    "start_date_partial": _g(startDate="2026-01"),
    "start_codeable_concept": _g(
        startCodeableConcept={"coding": [{"system": SCT, "code": "32485007"}]}
    ),
    "target_quantity": _g(
        target=[
            {
                "measure": {"coding": [{"system": LOINC, "code": "4548-4"}]},
                "detailQuantity": {"value": 7, "comparator": "<", "unit": "%"},
                "dueDate": "2026-12-31",
            }
        ]
    ),
    "target_range": _g(
        target=[
            {
                "measure": {"text": "weight"},
                "detailRange": {"low": {"value": 60}, "high": {"value": 70}},
                "dueDuration": {"value": 6, "unit": "mo"},
            }
        ]
    ),
    "target_codeable_concept": _g(
        target=[
            {
                "measure": {"text": "diet"},
                "detailCodeableConcept": {"text": "low sodium"},
            }
        ]
    ),
    "target_string_boolean_integer_ratio": _g(
        target=[
            {"measure": {"text": "a"}, "detailString": "lose 5kg"},
            {"measure": {"text": "b"}, "detailBoolean": True},
            {"measure": {"text": "c"}, "detailInteger": 5},
            {
                "measure": {"text": "d"},
                "detailRatio": {
                    "numerator": {"value": 1},
                    "denominator": {"value": 2},
                },
            },
        ]
    ),
    "status_date_and_reason": _g(statusDate="2026-01-20", statusReason="Agreed"),
    "expressed_by": _g(expressedBy={"reference": "Practitioner/30001"}),
    "addresses": _g(
        addresses=[
            {"reference": "Condition/120001"},
            {"reference": "NutritionOrder/9"},
            {"reference": "ServiceRequest/80001"},
        ]
    ),
    "note": _g(
        note=[
            {"text": "Agreed", "time": "2026-01-15T10:00:00Z"},
            {
                "text": "By a practitioner",
                "authorReference": {"reference": "Practitioner/30001"},
            },
            {"text": "By name", "authorString": "Dr A"},
        ]
    ),
    "outcome": _g(
        outcomeCode=[{"text": "improved"}],
        outcomeReference=[{"reference": "Observation/160001"}],
    ),
    "extension": _g(
        extension=[
            {
                "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                "valueString": "y",
            }
        ]
    ),
    "full": _g(
        identifier=[{"system": "urn:g", "value": "G-1"}],
        achievementStatus={"text": "in progress"},
        category=[{"text": "dietary"}],
        priority={"text": "high"},
        startDate="2026-01-15",
        target=[
            {
                "measure": {"text": "hba1c"},
                "detailQuantity": {"value": 7, "unit": "%"},
                "dueDate": "2026-12-31",
            }
        ],
        statusDate="2026-01-20",
        statusReason="Agreed",
        expressedBy={"reference": "Patient/10001"},
        addresses=[{"reference": "Condition/120001"}],
        note=[{"text": "n"}],
        outcomeCode=[{"text": "improved"}],
        outcomeReference=[{"reference": "Observation/160001"}],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_goal_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.Goal, to_fhir_goal(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {**BASE, "statusReason": "Agreed"}
    out = to_fhir_goal(_goal(content))
    assert out["resourceType"] == "Goal"
    assert out["id"] == "460001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `achievementStatus`, `priority` or `subject` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("lifecycleStatus with an unknown code", {"lifecycleStatus": "robot"}),
        ("lifecycleStatus as number", {"lifecycleStatus": 1}),
        ("description as string not a CodeableConcept", {"description": "x"}),
        ("subject as string not a Reference", {"subject": "Patient/1"}),
        ("achievementStatus as string", {"achievementStatus": "achieved"}),
        ("category as object not a list", {"category": {"text": "x"}}),
        ("priority as string", {"priority": "high"}),
        ("startDate not a date", {"startDate": "soon"}),
        ("startDate as number", {"startDate": 5}),
        ("target as object not a list", {"target": {"measure": {"text": "x"}}}),
        ("target dueDate not a date", {"target": [{"dueDate": "soon"}]}),
        ("target detailBoolean as string", {"target": [{"detailBoolean": "yes"}]}),
        ("target detailInteger as string", {"target": [{"detailInteger": "5"}]}),
        ("target measure as string", {"target": [{"measure": "hba1c"}]}),
        ("statusDate not a date", {"statusDate": "soon"}),
        ("statusReason as number", {"statusReason": 5}),
        ("expressedBy as string", {"expressedBy": "Patient/1"}),
        ("addresses as object not a list", {"addresses": {"reference": "Condition/1"}}),
        ("note as string", {"note": "x"}),
        ("outcomeCode as string", {"outcomeCode": "x"}),
        ("outcomeReference as string", {"outcomeReference": ["Observation/1"]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Goal", "id": "460001", **BASE, **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.Goal, validate=True
        )

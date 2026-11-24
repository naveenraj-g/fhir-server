"""FHIR R4 conformance for `to_fhir_plan_definition()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

PlanDefinition is stored whole in `content` (like ActivityDefinition, Questionnaire and the
other content-based resources): the resource lives in PlanDefinitionModel.content, and
to_fhir_plan_definition() only stamps `id` and `meta` onto it. So what can go wrong on the read
side is that stamping (e.g. a malformed meta extension) or a stored document the server returns
that isn't valid R4 - each case below is a `content` document as the write path would store it,
run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.plan_definition import to_fhir_plan_definition
from app.models.plan_definition import PlanDefinitionModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.plan_definition_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
SCT = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"
USAGE = "http://terminology.hl7.org/CodeSystem/usage-context-type"
TOPIC = "http://terminology.hl7.org/CodeSystem/definition-topic"
PD_TYPE = "http://terminology.hl7.org/CodeSystem/plan-definition-type"


def _c(content: dict, **overrides) -> PlanDefinitionModel:
    fields = {
        "plan_definition_id": 420001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return PlanDefinitionModel(**fields)


def _base(**extra) -> dict:
    return {"status": "active", **extra}


def _case(**extra) -> PlanDefinitionModel:
    return _c(_base(**extra))


CASES = {
    "minimal": _c(_base()),
    "updated_by_and_updated_at": _c(_base(), updated_by="u-other", updated_at=D),
    **{
        f"status_{s}": _case(status=s)
        for s in ("draft", "active", "retired", "unknown")
    },
    "url_version_name_title": _case(
        url="https://fhir-server.dev/fhir/PlanDefinition/x",
        version="1.0",
        name="Pathway",
        title="Discharge pathway",
        subtitle="After surgery",
        experimental=True,
    ),
    **{
        f"type_{t}": _case(type={"coding": [{"system": PD_TYPE, "code": t}]})
        for t in ("order-set", "clinical-protocol", "eca-rule", "workflow-definition")
    },
    "identifier_with_type_and_assigner": _case(
        identifier=[
            {
                "use": "official",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "ACSN",
                        }
                    ]
                },
                "system": "https://fhir-server.dev/fhir/identifier-system/plan-definition-id",
                "value": "PD-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "date_publisher_description": _case(
        date="2026-01-15T10:00:00Z",
        publisher="Example Health",
        description="Steps to **take** at discharge.",
        purpose="Discharge",
        usage="At discharge",
        copyright="(c) Example",
    ),
    "approval_and_review_dates": _case(
        approvalDate="2026-01-10", lastReviewDate="2026-01-12"
    ),
    "effective_period": _case(
        effectivePeriod={"start": "2026-01-01", "end": "2026-12-31"}
    ),
    "contact_and_roles": _case(
        contact=[
            {"name": "Help desk", "telecom": [{"system": "phone", "value": "555"}]}
        ],
        author=[{"name": "Dr A"}],
        editor=[{"name": "Dr B"}],
        reviewer=[{"name": "Dr C"}],
        endorser=[{"name": "Dr D"}],
    ),
    "use_context_every_value_kind": _case(
        useContext=[
            {
                "code": {"system": USAGE, "code": "focus"},
                "valueCodeableConcept": {
                    "coding": [{"system": SCT, "code": "35489007"}]
                },
            },
            {
                "code": {"system": USAGE, "code": "age"},
                "valueRange": {
                    "low": {"value": 12, "system": UCUM, "code": "a"},
                    "high": {"value": 17, "system": UCUM, "code": "a"},
                },
            },
            {
                "code": {"system": USAGE, "code": "venue"},
                "valueQuantity": {
                    "value": 5,
                    "unit": "mg",
                    "system": UCUM,
                    "code": "mg",
                },
            },
            {
                "code": {"system": USAGE, "code": "workflow"},
                "valueReference": {"reference": "Organization/190001"},
            },
        ]
    ),
    "jurisdiction_and_topic": _case(
        jurisdiction=[{"coding": [{"system": "urn:iso:std:iso:3166", "code": "US"}]}],
        topic=[{"coding": [{"system": TOPIC, "code": "treatment"}]}, {"text": "x"}],
    ),
    "related_artifacts": _case(
        relatedArtifact=[
            {
                "type": "documentation",
                "display": "Guide",
                "url": "http://example.org/g",
            },
            {
                "type": "predecessor",
                "resource": "http://example.org/PlanDefinition/old",
            },
            {"type": "composed-of", "resource": "http://example.org/Library/x|1.0"},
            {"type": "citation", "citation": "A. Author. 2020."},
        ],
        library=["http://example.org/Library/lib1"],
    ),
    "subject_codeable_concept": _case(subjectCodeableConcept={"text": "adults"}),
    "subject_reference": _case(subjectReference={"reference": "Group/430001"}),
    "goal": _case(
        goal=[
            {
                "category": {"text": "behavioral"},
                "description": {"text": "Walk daily"},
                "priority": {"text": "high"},
                "start": {"text": "discharge"},
                "addresses": [{"text": "mobility"}],
                "documentation": [{"type": "documentation", "display": "Guide"}],
                "target": [
                    {
                        "measure": {"text": "steps"},
                        "detailQuantity": {"value": 4000, "unit": "steps"},
                        "due": {"value": 30, "unit": "d", "system": UCUM, "code": "d"},
                    },
                    {
                        "measure": {"text": "range"},
                        "detailRange": {"low": {"value": 1}},
                    },
                    {"detailCodeableConcept": {"text": "done"}},
                ],
            }
        ]
    ),
    "action_tree": _case(
        action=[
            {
                "prefix": "1",
                "title": "Discharge checks",
                "description": "Run the checks",
                "textEquivalent": "checks",
                "priority": "routine",
                "code": [{"text": "x"}],
                "reason": [{"text": "why"}],
                "documentation": [{"type": "documentation", "display": "Guide"}],
                "goalId": ["g1"],
                "subjectCodeableConcept": {"text": "adults"},
                "trigger": [{"type": "named-event", "name": "discharge"}],
                "condition": [
                    {
                        "kind": "applicability",
                        "expression": {"language": "text/cql", "expression": "Adult()"},
                    }
                ],
                "input": [{"type": "Patient"}],
                "output": [{"type": "Encounter"}],
                "relatedAction": [
                    {
                        "actionId": "a0",
                        "relationship": "after-end",
                        "offsetDuration": {"value": 1, "unit": "d"},
                    }
                ],
                "timingDateTime": "2026-02-01T09:00:00Z",
                "participant": [{"type": "practitioner"}],
                "type": {"coding": [{"code": "create"}]},
                "groupingBehavior": "logical-group",
                "selectionBehavior": "exactly-one",
                "requiredBehavior": "must",
                "precheckBehavior": "yes",
                "cardinalityBehavior": "single",
                "action": [
                    {
                        "title": "Book a visit",
                        "definitionCanonical": "http://example.org/ActivityDefinition/visit|1.0",
                        "transform": "http://example.org/StructureMap/t1",
                        "dynamicValue": [
                            {
                                "path": "title",
                                "expression": {
                                    "language": "text/fhirpath",
                                    "expression": "'x'",
                                },
                            }
                        ],
                    },
                    {
                        "title": "Uri definition",
                        "definitionUri": "http://example.org/thing",
                    },
                    {"title": "Period", "timingPeriod": {"start": "2026-01-01"}},
                    {
                        "title": "Age",
                        "timingAge": {
                            "value": 3,
                            "unit": "years",
                            "system": UCUM,
                            "code": "a",
                        },
                    },
                    {
                        "title": "Range",
                        "timingRange": {"low": {"value": 1}, "high": {"value": 2}},
                    },
                    {
                        "title": "Duration",
                        "timingDuration": {
                            "value": 4,
                            "unit": "h",
                            "system": UCUM,
                            "code": "h",
                        },
                    },
                    {"title": "Timing", "timingTiming": {"repeat": {"frequency": 1}}},
                ],
            }
        ]
    ),
    "extension": _case(
        extension=[
            {
                "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                "valueString": "y",
            }
        ]
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_plan_definition_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.PlanDefinition, to_fhir_plan_definition(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = _base(name="Pathway", action=[{"title": "x", "action": [{"title": "y"}]}])
    out = to_fhir_plan_definition(_c(content))
    assert out["resourceType"] == "PlanDefinition"
    assert out["id"] == "420001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `type` or `subjectReference` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("url as number", {"url": 5}),
        ("type as string", {"type": "order-set"}),
        ("experimental as string", {"experimental": "yes"}),
        ("date not a dateTime", {"date": "yesterday"}),
        ("approvalDate not a date", {"approvalDate": "not-a-date"}),
        ("contact as object not a list", {"contact": {"name": "x"}}),
        ("useContext as string", {"useContext": "x"}),
        (
            "useContext entry without a code",
            {"useContext": [{"valueReference": {"reference": "Patient/1"}}]},
        ),
        ("jurisdiction as string", {"jurisdiction": "US"}),
        ("topic as object not a list", {"topic": {"text": "x"}}),
        ("effectivePeriod as string", {"effectivePeriod": "2026"}),
        ("relatedArtifact as object", {"relatedArtifact": {"type": "x"}}),
        (
            "relatedArtifact with an unknown type",
            {"relatedArtifact": [{"type": "banana"}]},
        ),
        ("library as string", {"library": "http://x"}),
        ("goal as object not a list", {"goal": {"description": {"text": "x"}}}),
        ("goal without a description", {"goal": [{"category": {"text": "x"}}]}),
        ("action as object not a list", {"action": {"title": "x"}}),
        ("action title as number", {"action": [{"title": 5}]}),
        ("action priority with an unknown code", {"action": [{"priority": "now"}]}),
        (
            "action groupingBehavior unknown",
            {"action": [{"groupingBehavior": "banana"}]},
        ),
        (
            "action selectionBehavior unknown",
            {"action": [{"selectionBehavior": "banana"}]},
        ),
        (
            "action condition without a kind",
            {"action": [{"condition": [{"expression": {"language": "x"}}]}]},
        ),
        ("nested action not a list", {"action": [{"action": {"title": "x"}}]}),
        (
            "action timingDateTime not a dateTime",
            {"action": [{"timingDateTime": "tomorrow"}]},
        ),
        (
            "action participant without a type",
            {"action": [{"participant": [{"role": {"text": "x"}}]}]},
        ),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "PlanDefinition", "id": "420001", **_base(), **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.PlanDefinition, validate=True
        )

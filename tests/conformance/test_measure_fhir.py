"""FHIR R4 conformance for `to_fhir_measure()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Measure is stored whole in `content` (like ActivityDefinition, PlanDefinition and the other
content-based resources): the resource lives in MeasureModel.content, and to_fhir_measure() only
stamps `id` and `meta` onto it. So what can go wrong on the read side is that stamping (e.g. a
malformed meta extension) or a stored document the server returns that isn't valid R4 - each case
below is a `content` document as the write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.measure import to_fhir_measure
from app.models.measure import MeasureModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.measure_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
SCT = "http://snomed.info/sct"
UCUM = "http://unitsofmeasure.org"
USAGE = "http://terminology.hl7.org/CodeSystem/usage-context-type"
TOPIC = "http://terminology.hl7.org/CodeSystem/definition-topic"
POPULATION = "http://terminology.hl7.org/CodeSystem/measure-population"
CQL = {"language": "text/cql", "expression": "Initial Population"}


def _c(content: dict, **overrides) -> MeasureModel:
    fields = {
        "measure_id": 560001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return MeasureModel(**fields)


def _base(**extra) -> dict:
    return {"status": "active", **extra}


def _case(**extra) -> MeasureModel:
    return _c(_base(**extra))


CASES = {
    "minimal": _c(_base()),
    "updated_by_and_updated_at": _c(_base(), updated_by="u-other", updated_at=D),
    **{
        f"status_{s}": _case(status=s)
        for s in ("draft", "active", "retired", "unknown")
    },
    "url_version_name_title": _case(
        url="https://fhir-server.dev/fhir/Measure/x",
        version="1.0",
        name="Readmission",
        title="30-day readmission",
        subtitle="Adults",
        experimental=True,
    ),
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
                "system": "https://fhir-server.dev/fhir/identifier-system/measure-id",
                "value": "M-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "date_publisher_description": _case(
        date="2026-01-15T10:00:00Z",
        publisher="Example Health",
        description="Readmissions within **30 days**.",
        purpose="Quality",
        usage="Reporting",
        copyright="(c) Example",
        disclaimer="For research use",
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
            {"type": "predecessor", "resource": "http://example.org/Measure/old"},
            {"type": "composed-of", "resource": "http://example.org/Library/x|1.0"},
            {"type": "citation", "citation": "A. Author. 2020."},
        ],
        library=["http://example.org/Library/lib1"],
    ),
    "subject_codeable_concept": _case(subjectCodeableConcept={"text": "adults"}),
    "subject_reference": _case(subjectReference={"reference": "Group/430001"}),
    "scoring_and_notation": _case(
        scoring={
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/measure-scoring",
                    "code": "proportion",
                }
            ]
        },
        compositeScoring={"text": "linear"},
        type=[{"text": "process"}, {"text": "outcome"}],
        improvementNotation={"text": "increase"},
    ),
    "narrative_elements": _case(
        riskAdjustment="By age",
        rateAggregation="Weighted",
        rationale="Reduces readmissions",
        clinicalRecommendationStatement="Follow up within 7 days",
        definition=["Readmission: an unplanned return"],
        guidance="Use the discharge date",
    ),
    "group_population_and_stratifier": _case(
        group=[
            {
                "id": "g1",
                "code": {"text": "overall"},
                "description": "Overall",
                "population": [
                    {
                        "code": {
                            "coding": [
                                {"system": POPULATION, "code": "initial-population"}
                            ]
                        },
                        "description": "All discharges",
                        "criteria": CQL,
                    },
                    {"code": {"text": "numerator"}, "criteria": CQL},
                ],
                "stratifier": [
                    {"code": {"text": "age"}, "criteria": CQL},
                    {
                        "code": {"text": "multi"},
                        "component": [
                            {"code": {"text": "sex"}, "criteria": CQL},
                            {
                                "code": {"text": "ward"},
                                "description": "Ward",
                                "criteria": CQL,
                            },
                        ],
                    },
                ],
            },
            {"description": "second"},
        ]
    ),
    "supplemental_data": _case(
        supplementalData=[
            {
                "code": {"text": "race"},
                "usage": [
                    {"text": "supplemental-data"},
                    {"text": "risk-adjustment-factor"},
                ],
                "description": "Race",
                "criteria": CQL,
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
def test_measure_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.Measure, to_fhir_measure(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = _base(name="Readmission", group=[{"description": "g"}])
    out = to_fhir_measure(_c(content))
    assert out["resourceType"] == "Measure"
    assert out["id"] == "560001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `scoring` or `subjectReference` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("url as number", {"url": 5}),
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
        ("disclaimer as number", {"disclaimer": 5}),
        ("scoring as string", {"scoring": "proportion"}),
        ("compositeScoring as string", {"compositeScoring": "linear"}),
        ("type as object not a list", {"type": {"text": "process"}}),
        ("riskAdjustment as number", {"riskAdjustment": 5}),
        ("improvementNotation as string", {"improvementNotation": "increase"}),
        ("definition as string", {"definition": "x"}),
        ("group as object not a list", {"group": {"description": "x"}}),
        (
            "group population as object",
            {"group": [{"population": {"description": "x"}}]},
        ),
        (
            "population without a criteria",
            {"group": [{"population": [{"description": "x"}]}]},
        ),
        (
            "stratifier component as object",
            {"group": [{"stratifier": [{"component": {"description": "x"}}]}]},
        ),
        ("supplementalData as object", {"supplementalData": {"code": {"text": "x"}}}),
        (
            "supplementalData without a criteria",
            {"supplementalData": [{"code": {"text": "x"}}]},
        ),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Measure", "id": "560001", **_base(), **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.Measure, validate=True
        )

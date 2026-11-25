"""FHIR R4 conformance for `to_fhir_activity_definition()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

ActivityDefinition is stored whole in `content` (like Questionnaire, CarePlan and the other
content-based resources): the resource lives in ActivityDefinitionModel.content, and
to_fhir_activity_definition() only stamps `id` and `meta` onto it. So what can go wrong on the
read side is that stamping (e.g. a malformed meta extension) or a stored document the server
returns that isn't valid R4 - each case below is a `content` document as the write path would
store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.activity_definition import to_fhir_activity_definition
from app.models.activity_definition import ActivityDefinitionModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.activity_definition_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
SCT = "http://snomed.info/sct"
LOINC = "http://loinc.org"
UCUM = "http://unitsofmeasure.org"
USAGE = "http://terminology.hl7.org/CodeSystem/usage-context-type"
TOPIC = "http://terminology.hl7.org/CodeSystem/definition-topic"


def _c(content: dict, **overrides) -> ActivityDefinitionModel:
    fields = {
        "activity_definition_id": 410001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return ActivityDefinitionModel(**fields)


def _base(**extra) -> dict:
    return {"status": "active", **extra}


def _case(**extra) -> ActivityDefinitionModel:
    return _c(_base(**extra))


CASES = {
    "minimal": _c(_base()),
    "updated_by_and_updated_at": _c(_base(), updated_by="u-other", updated_at=D),
    **{
        f"status_{s}": _case(status=s)
        for s in ("draft", "active", "retired", "unknown")
    },
    "url_version_name_title": _case(
        url="https://fhir-server.dev/fhir/ActivityDefinition/x",
        version="1.0",
        name="FollowUp",
        title="Follow-up visit",
        subtitle="Book it",
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
                "system": "https://fhir-server.dev/fhir/identifier-system/activity-definition-id",
                "value": "AD-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "date_publisher_description": _case(
        date="2026-01-15T10:00:00Z",
        publisher="Example Health",
        description="Book a **follow-up** visit.",
        purpose="Follow-up",
        usage="After discharge",
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
                "resource": "http://example.org/ActivityDefinition/old",
            },
            {"type": "composed-of", "resource": "http://example.org/Library/x|1.0"},
            {"type": "citation", "citation": "A. Author. 2020."},
        ],
        library=["http://example.org/Library/lib1"],
    ),
    "subject_codeable_concept": _case(subjectCodeableConcept={"text": "adults"}),
    "subject_reference": _case(subjectReference={"reference": "Group/430001"}),
    "kind_profile_code": _case(
        kind="ServiceRequest",
        profile="http://example.org/StructureDefinition/my-request",
        code={"coding": [{"system": LOINC, "code": "44249-1"}]},
        intent="order",
        priority="routine",
        doNotPerform=False,
    ),
    **{
        f"intent_{i}": _case(intent=i)
        for i in (
            "proposal",
            "plan",
            "directive",
            "order",
            "original-order",
            "reflex-order",
            "filler-order",
            "instance-order",
            "option",
        )
    },
    **{
        f"priority_{p}": _case(priority=p)
        for p in ("routine", "urgent", "asap", "stat")
    },
    "timing_timing": _case(
        timingTiming={"repeat": {"frequency": 1, "period": 1, "periodUnit": "d"}}
    ),
    "timing_date_time": _case(timingDateTime="2026-02-01T09:00:00Z"),
    "timing_age": _case(
        timingAge={"value": 3, "unit": "years", "system": UCUM, "code": "a"}
    ),
    "timing_period": _case(timingPeriod={"start": "2026-01-01", "end": "2026-02-01"}),
    "timing_range": _case(timingRange={"low": {"value": 1}, "high": {"value": 2}}),
    "timing_duration": _case(
        timingDuration={"value": 4, "unit": "h", "system": UCUM, "code": "h"}
    ),
    "location_and_participant": _case(
        location={"reference": "Location/230001"},
        participant=[
            {"type": "practitioner", "role": {"text": "nurse"}},
            {"type": "patient"},
        ],
    ),
    "product_reference": _case(productReference={"reference": "Medication/250001"}),
    "product_codeable_concept": _case(productCodeableConcept={"text": "saline"}),
    "quantity_and_dosage": _case(
        quantity={"value": 2, "unit": "mL"},
        dosage=[{"sequence": 1, "text": "2 mL once", "route": {"text": "oral"}}],
        bodySite=[{"text": "arm"}],
    ),
    "requirements": _case(
        specimenRequirement=[{"reference": "SpecimenDefinition/550001"}],
        observationRequirement=[{"reference": "ObservationDefinition/400001"}],
        observationResultRequirement=[{"reference": "ObservationDefinition/400002"}],
    ),
    "transform_and_dynamic_values": _case(
        transform="http://example.org/StructureMap/t1",
        dynamicValue=[
            {
                "path": "priority",
                "expression": {"language": "text/cql", "expression": "Urgent()"},
            }
        ],
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
def test_activity_definition_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.ActivityDefinition, to_fhir_activity_definition(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = _base(name="FollowUp", priority="stat", dosage=[{"text": "x"}])
    out = to_fhir_activity_definition(_c(content))
    assert out["resourceType"] == "ActivityDefinition"
    assert out["id"] == "410001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `code`, `location` or `quantity` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("kind with an unknown code", {"kind": "Banana"}),
        ("intent with an unknown code", {"intent": "maybe"}),
        ("priority with an unknown code", {"priority": "now"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("url as number", {"url": 5}),
        ("experimental as string", {"experimental": "yes"}),
        ("date not a dateTime", {"date": "yesterday"}),
        ("approvalDate with a time", {"approvalDate": "not-a-date"}),
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
        ("doNotPerform as string", {"doNotPerform": "maybe"}),
        ("timingDateTime not a dateTime", {"timingDateTime": "tomorrow"}),
        ("location as string", {"location": "Location/1"}),
        ("participant as object", {"participant": {"type": "patient"}}),
        ("participant with an unknown type", {"participant": [{"type": "banana"}]}),
        ("quantity as string", {"quantity": "2 mL"}),
        ("dosage as object not a list", {"dosage": {"text": "x"}}),
        ("bodySite as object", {"bodySite": {"text": "x"}}),
        (
            "specimenRequirement as object",
            {"specimenRequirement": {"reference": "SpecimenDefinition/1"}},
        ),
        ("dynamicValue as object", {"dynamicValue": {"path": "x"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "ActivityDefinition",
        "id": "410001",
        **_base(),
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.ActivityDefinition, validate=True
        )

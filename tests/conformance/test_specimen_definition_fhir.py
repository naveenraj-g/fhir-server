"""FHIR R4 conformance for `to_fhir_specimen_definition()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

SpecimenDefinition is stored whole in `content` (like the other content-based resources): the
resource lives in SpecimenDefinitionModel.content, and to_fhir_specimen_definition() only stamps
`id` and `meta` onto it. So what can go wrong on the read side is that stamping (e.g. a malformed
meta extension) or a stored document the server returns that isn't valid R4 - each case below is a
`content` document as the write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.specimen_definition import to_fhir_specimen_definition
from app.models.specimen_definition import SpecimenDefinitionModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.specimen_definition_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
V2_0487 = "http://terminology.hl7.org/CodeSystem/v2-0487"
UCUM = "http://unitsofmeasure.org"


def _c(content: dict, **overrides) -> SpecimenDefinitionModel:
    fields = {
        "specimen_definition_id": 550001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return SpecimenDefinitionModel(**fields)


def _tested(**extra) -> dict:
    return {"preference": "preferred", **extra}


CASES = {
    "empty": _c({}),
    "updated_by_and_updated_at": _c({}, updated_by="u-other", updated_at=D),
    "identifier_with_type_and_assigner": _c(
        {
            "identifier": {
                "use": "official",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "ACSN",
                        }
                    ]
                },
                "system": "https://fhir-server.dev/fhir/identifier-system/specimen-definition-id",
                "value": "SD-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        }
    ),
    "type_collected": _c(
        {
            "typeCollected": {
                "coding": [{"system": V2_0487, "code": "BLD", "display": "Blood"}]
            }
        }
    ),
    "preparation_time_aspect_and_collection": _c(
        {
            "patientPreparation": [{"text": "Fasting"}, {"coding": [{"code": "x"}]}],
            "timeAspect": "Morning",
            "collection": [{"text": "Venipuncture"}],
        }
    ),
    **{
        f"preference_{p}": _c({"typeTested": [_tested(preference=p)]})
        for p in ("preferred", "alternate")
    },
    "type_tested_simple": _c(
        {
            "typeTested": [
                _tested(
                    isDerived=False,
                    type={"text": "Whole blood"},
                    requirement="Keep cold",
                    retentionTime={
                        "value": 7,
                        "unit": "d",
                        "system": UCUM,
                        "code": "d",
                    },
                )
            ]
        }
    ),
    "container_every_element": _c(
        {
            "typeTested": [
                _tested(
                    container={
                        "material": {"text": "glass"},
                        "type": {"coding": [{"system": V2_0487, "code": "SPECIMEN"}]},
                        "cap": {"text": "purple"},
                        "description": "EDTA tube",
                        "capacity": {
                            "value": 5,
                            "unit": "mL",
                            "system": UCUM,
                            "code": "mL",
                        },
                        "minimumVolumeQuantity": {"value": 1, "unit": "mL"},
                        "additive": [
                            {"additiveCodeableConcept": {"text": "EDTA"}},
                            {"additiveReference": {"reference": "Substance/1"}},
                        ],
                        "preparation": "Mix gently",
                    }
                )
            ]
        }
    ),
    "container_minimum_volume_string": _c(
        {"typeTested": [_tested(container={"minimumVolumeString": "about 1 mL"})]}
    ),
    "rejection_criteria": _c(
        {
            "typeTested": [
                _tested(rejectionCriterion=[{"text": "hemolyzed"}, {"text": "clotted"}])
            ]
        }
    ),
    "handling": _c(
        {
            "typeTested": [
                _tested(
                    handling=[
                        {
                            "temperatureQualifier": {"text": "refrigerated"},
                            "temperatureRange": {
                                "low": {"value": 2, "unit": "Cel"},
                                "high": {"value": 8, "unit": "Cel"},
                            },
                            "maxDuration": {"value": 24, "unit": "h"},
                            "instruction": "Do not freeze",
                        },
                        {"instruction": "Protect from light"},
                    ]
                )
            ]
        }
    ),
    "several_types_tested": _c(
        {"typeTested": [_tested(), _tested(preference="alternate", isDerived=True)]}
    ),
    "extension": _c(
        {
            "extension": [
                {
                    "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                    "valueString": "y",
                }
            ]
        }
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_specimen_definition_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.SpecimenDefinition, to_fhir_specimen_definition(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {"timeAspect": "Morning", "typeTested": [_tested()]}
    out = to_fhir_specimen_definition(_c(content))
    assert out["resourceType"] == "SpecimenDefinition"
    assert out["id"] == "550001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `identifier` or `typeCollected` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("identifier as string", {"identifier": "SD-1"}),
        ("typeCollected as string", {"typeCollected": "BLD"}),
        ("patientPreparation as object", {"patientPreparation": {"text": "x"}}),
        ("timeAspect as number", {"timeAspect": 5}),
        ("collection as string", {"collection": "x"}),
        ("typeTested as object", {"typeTested": {"preference": "preferred"}}),
        ("typeTested without a preference", {"typeTested": [{"isDerived": True}]}),
        ("preference with an unknown code", {"typeTested": [{"preference": "banana"}]}),
        (
            "isDerived as string",
            {"typeTested": [{"preference": "preferred", "isDerived": "yes"}]},
        ),
        (
            "typeTested type as string",
            {"typeTested": [{"preference": "preferred", "type": "x"}]},
        ),
        (
            "container capacity as string",
            {
                "typeTested": [
                    {"preference": "preferred", "container": {"capacity": "5 mL"}}
                ]
            },
        ),
        (
            "additive as object",
            {
                "typeTested": [
                    {
                        "preference": "preferred",
                        "container": {"additive": {"additiveCodeableConcept": {}}},
                    }
                ]
            },
        ),
        (
            "additive without its choice",
            {
                "typeTested": [
                    {"preference": "preferred", "container": {"additive": [{}]}}
                ]
            },
        ),
        (
            "retentionTime as string",
            {"typeTested": [{"preference": "preferred", "retentionTime": "7 days"}]},
        ),
        (
            "rejectionCriterion as object",
            {
                "typeTested": [
                    {"preference": "preferred", "rejectionCriterion": {"text": "x"}}
                ]
            },
        ),
        (
            "handling as object",
            {
                "typeTested": [
                    {"preference": "preferred", "handling": {"instruction": "x"}}
                ]
            },
        ),
        (
            "handling instruction as number",
            {
                "typeTested": [
                    {"preference": "preferred", "handling": [{"instruction": 5}]}
                ]
            },
        ),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "SpecimenDefinition", "id": "550001", **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.SpecimenDefinition, validate=True
        )

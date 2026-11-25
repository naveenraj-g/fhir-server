"""FHIR R4 conformance for `to_fhir_group()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Group is stored Medplum-style (like Patient, Appointment, Encounter, Condition, Procedure,
Specimen, ServiceRequest, Medication and the other content-based resources): the resource lives
whole in GroupModel.content, and to_fhir_group() only stamps `id` and `meta` onto it. So what
can go wrong on the read side is that stamping (e.g. a malformed meta extension) or a stored
document the server returns that isn't valid R4 - each case below is a `content` document as
the write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.group import to_fhir_group
from app.models.group import GroupModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.group_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
SCT = "http://snomed.info/sct"
BASE = {"type": "person", "actual": True}
CODE = {"coding": [{"system": SCT, "code": "385093006", "display": "Community"}]}


def _g(content: dict, **overrides) -> GroupModel:
    fields = {
        "group_id": 430001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return GroupModel(**fields)


def _with(**extra) -> GroupModel:
    return _g({**BASE, **extra})


def _char(**value):
    return {"code": CODE, "exclude": False, **value}


CASES = {
    "minimal": _g(BASE),
    "updated_by_and_updated_at": _g(BASE, updated_by="u-other", updated_at=D),
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
                "system": "https://fhir-server.dev/fhir/identifier-system/group-id",
                "value": "GRP-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    **{
        f"type_{t}": _g({"type": t, "actual": False})
        for t in (
            "person",
            "animal",
            "practitioner",
            "device",
            "medication",
            "substance",
        )
    },
    "actual_false": _g({"type": "person", "actual": False}),
    "active": _with(active=True),
    "code": _with(code=CODE),
    "name_and_quantity": _with(name="Cohort", quantity=3),
    **{
        f"managing_entity_{t}": _with(managingEntity={"reference": f"{t}/1"})
        for t in ("Organization", "RelatedPerson", "Practitioner", "PractitionerRole")
    },
    "managing_entity_logical": _with(
        managingEntity={
            "identifier": {"system": "urn:mgr", "value": "M-9"},
            "display": "X",
        }
    ),
    "managing_entity_absolute_url": _with(
        managingEntity={"reference": "https://other.example.org/fhir/Organization/7"}
    ),
    "characteristic_codeable_concept": _with(
        characteristic=[
            _char(valueCodeableConcept={"coding": [{"system": SCT, "code": "1"}]})
        ]
    ),
    "characteristic_boolean": _with(characteristic=[_char(valueBoolean=True)]),
    "characteristic_quantity": _with(
        characteristic=[_char(valueQuantity={"value": 180, "unit": "cm"})]
    ),
    "characteristic_range": _with(
        characteristic=[
            _char(
                valueRange={
                    "low": {"value": 150, "unit": "cm"},
                    "high": {"value": 190, "unit": "cm"},
                }
            )
        ]
    ),
    "characteristic_reference": _with(
        characteristic=[_char(valueReference={"reference": "Observation/160001"})]
    ),
    "characteristic_excluded_with_period": _with(
        characteristic=[
            {
                "code": CODE,
                "valueBoolean": True,
                "exclude": True,
                "period": {"start": "2023-01-01", "end": "2023-12-31"},
            }
        ]
    ),
    "member": _with(
        member=[
            {"entity": {"reference": "Patient/10001"}},
            {"entity": {"reference": "Group/430000"}, "inactive": True},
        ]
    ),
    **{
        f"member_{t}": _with(member=[{"entity": {"reference": f"{t}/1"}}])
        for t in (
            "Patient",
            "Practitioner",
            "PractitionerRole",
            "Device",
            "Medication",
            "Substance",
            "Group",
        )
    },
    "member_with_period": _with(
        member=[
            {
                "entity": {"reference": "Patient/10001"},
                "period": {"start": "2023-01-01"},
            }
        ]
    ),
    "member_logical": _with(
        member=[{"entity": {"identifier": {"system": "urn:pts", "value": "P-9"}}}]
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
        identifier=[{"system": "urn:g", "value": "GRP-1"}],
        active=True,
        code=CODE,
        name="Cohort",
        quantity=2,
        managingEntity={"reference": "Organization/190001"},
        characteristic=[_char(valueBoolean=False)],
        member=[{"entity": {"reference": "Patient/10001"}}],
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_group_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.Group, to_fhir_group(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {**BASE, "name": "Cohort", "quantity": 2}
    out = to_fhir_group(_g(content))
    assert out["resourceType"] == "Group"
    assert out["id"] == "430001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `code` or `managingEntity` as a one-item list; the integration
# tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("type with an unknown code", {"type": "robot"}),
        ("type as number", {"type": 1}),
        ("actual as string", {"actual": "yes"}),
        ("active as string", {"active": "yes"}),
        ("code as string not a CodeableConcept", {"code": "x"}),
        ("name as number", {"name": 5}),
        ("quantity as string", {"quantity": "many"}),
        ("quantity negative", {"quantity": -1}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("managingEntity as string", {"managingEntity": "Organization/1"}),
        ("characteristic as object not a list", {"characteristic": {"exclude": False}}),
        (
            "characteristic code as string",
            {"characteristic": [{"code": "x", "exclude": False}]},
        ),
        (
            "characteristic exclude as string",
            {"characteristic": [{"code": CODE, "exclude": "no"}]},
        ),
        (
            "characteristic valueBoolean as string",
            {
                "characteristic": [
                    {"code": CODE, "valueBoolean": "yes", "exclude": False}
                ]
            },
        ),
        (
            "characteristic valueRange as string",
            {"characteristic": [{"code": CODE, "valueRange": "1-3", "exclude": False}]},
        ),
        (
            "characteristic period as string",
            {
                "characteristic": [
                    {
                        "code": CODE,
                        "valueBoolean": True,
                        "exclude": False,
                        "period": "2023",
                    }
                ]
            },
        ),
        (
            "member as object not a list",
            {"member": {"entity": {"reference": "Patient/1"}}},
        ),
        ("member entity as string", {"member": [{"entity": "Patient/1"}]}),
        (
            "member inactive as string",
            {"member": [{"entity": {"reference": "Patient/1"}, "inactive": "no"}]},
        ),
        (
            "member period as string",
            {"member": [{"entity": {"reference": "Patient/1"}, "period": "2023"}]},
        ),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Group", "id": "430001", **BASE, **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.Group, validate=True
        )

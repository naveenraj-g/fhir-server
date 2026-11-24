"""FHIR R4 conformance for `to_fhir_flag()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Flag is stored content-based (like Goal, Task, CarePlan and the other rebuilt resources): the
resource lives whole in FlagModel.content, and to_fhir_flag() only stamps `id` and `meta` onto it.
So what can go wrong on the read side is that stamping (e.g. a malformed meta extension) or a
stored document the server returns that isn't valid R4 - each case below is a `content` document
as the write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.flag import to_fhir_flag
from app.models.flag import FlagModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.flag_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
SCT = "http://snomed.info/sct"
BASE = {
    "status": "active",
    "code": {"text": "Latex allergy"},
    "subject": {"reference": "Patient/10001"},
}


def _flag(content: dict, **overrides) -> FlagModel:
    fields = {
        "flag_id": 450001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return FlagModel(**fields)


def _f(**extra) -> FlagModel:
    return _flag({**BASE, **extra})


CASES = {
    "minimal": _flag(BASE),
    "updated_by_and_updated_at": _flag(BASE, updated_by="u-other", updated_at=D),
    **{f"status_{s}": _f(status=s) for s in ("active", "inactive", "entered-in-error")},
    "identifier_with_type_and_assigner": _f(
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
                "system": "https://fhir-server.dev/fhir/identifier-system/flag-id",
                "value": "F-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "category": _f(
        category=[
            {"text": "safety"},
            {"coding": [{"system": SCT, "code": "1", "display": "Behavioral"}]},
        ]
    ),
    "code_coded": _f(
        code={"coding": [{"system": SCT, "code": "300916003", "display": "Latex"}]}
    ),
    **{
        f"subject_{t.lower()}": _f(subject={"reference": f"{t}/1"})
        for t in (
            "Patient",
            "Location",
            "Group",
            "Organization",
            "Practitioner",
            "PlanDefinition",
            "Medication",
            "Procedure",
        )
    },
    "subject_logical": _f(
        subject={"identifier": {"system": "urn:mrn", "value": "M-9"}, "display": "Jane"}
    ),
    "subject_absolute_url": _f(
        subject={"reference": "https://other.example.org/fhir/Patient/1"}
    ),
    "period": _f(period={"start": "2026-01-15", "end": "2026-12-31"}),
    "period_open": _f(period={"start": "2026-01-15T09:00:00Z"}),
    "encounter": _f(encounter={"reference": "Encounter/20001"}),
    **{
        f"author_{t.lower()}": _f(author={"reference": f"{t}/1"})
        for t in (
            "Device",
            "Organization",
            "Patient",
            "Practitioner",
            "PractitionerRole",
        )
    },
    "extension": _f(
        extension=[
            {
                "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                "valueString": "y",
            }
        ]
    ),
    "full": _f(
        identifier=[{"system": "urn:f", "value": "F-1"}],
        category=[{"text": "safety"}],
        period={"start": "2026-01-15"},
        encounter={"reference": "Encounter/20001"},
        author={"reference": "Practitioner/30001"},
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_flag_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.Flag, to_fhir_flag(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {**BASE, "period": {"start": "2026-01-15"}}
    out = to_fhir_flag(_flag(content))
    assert out["resourceType"] == "Flag"
    assert out["id"] == "450001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `code`, `subject` or `period` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("code as string not a CodeableConcept", {"code": "x"}),
        ("category as object not a list", {"category": {"text": "x"}}),
        ("category entry as string", {"category": ["x"]}),
        ("subject as string not a Reference", {"subject": "Patient/1"}),
        ("period as string", {"period": "today"}),
        ("period start not a dateTime", {"period": {"start": "soon"}}),
        ("encounter as string", {"encounter": "Encounter/1"}),
        ("author as string", {"author": "Practitioner/1"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("identifier value as number", {"identifier": [{"value": 5}]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Flag", "id": "450001", **BASE, **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.Flag, validate=True
        )

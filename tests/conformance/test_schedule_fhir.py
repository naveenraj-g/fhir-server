"""FHIR R4 conformance for `to_fhir_schedule()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Schedule is stored Medplum-style (like Organization/Practitioner/
HealthcareService/Endpoint/PractitionerRole): the resource lives whole in
ScheduleModel.content, and to_fhir_schedule() only stamps `id` and `meta` onto
it. So what can go wrong on the read side is that stamping (e.g. a malformed
meta extension) or a stored document the server returns that isn't valid R4 —
each case below is a `content` document as the write path would store it, run
through the real read mapper. (R4 requires at least one `actor`, so every case
carries one.)
"""

import datetime as dt

import pytest

from app.fhir.mappers.schedule import to_fhir_schedule
from app.models.schedule import ScheduleModel
from tests.integration.schedule.support import FULL, MINIMAL

from .support import assert_valid, fhir_json_text

schedule_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.schedule_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
ACTOR = [{"reference": "Practitioner/30001"}]


def _stored(document: dict) -> dict:
    """What the write path stores: everything but resourceType/id/meta."""
    return {
        k: v for k, v in document.items() if k not in ("resourceType", "id", "meta")
    }


def _schedule(content: dict, **overrides) -> ScheduleModel:
    fields = {
        "schedule_id": 200001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": {"actor": ACTOR, **content},
    }
    fields.update(overrides)
    return ScheduleModel(**fields)


CASES = {
    "minimal": _schedule({"active": True}),
    "active_false": _schedule({"active": False}),
    "updated_by_and_updated_at": _schedule(
        {"active": True}, updated_by="u-other", updated_at=D
    ),
    "planning_horizon": _schedule(
        {
            "planningHorizon": {
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-12-31T23:59:59Z",
            }
        }
    ),
    "open_ended_planning_horizon": _schedule(
        {"planningHorizon": {"start": "2026-01-01"}}
    ),
    "identifier_with_type_and_assigner": _schedule(
        {
            "identifier": [
                {
                    "use": "official",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "SCH",
                            }
                        ]
                    },
                    "system": "https://fhir-server.dev/fhir/identifier-system/schedule-id",
                    "value": "S-1",
                    "assigner": {"reference": "Organization/190001"},
                }
            ]
        }
    ),
    "categories_types_and_specialties": _schedule(
        {
            "serviceCategory": [
                {
                    "coding": [{"code": "17", "display": "General Practice"}],
                    "text": "General",
                }
            ],
            "serviceType": [{"coding": [{"code": "124"}]}, {"text": "Free text only"}],
            "specialty": [{"coding": [{"code": "394579002", "display": "Cardiology"}]}],
        }
    ),
    "every_kind_of_actor": _schedule(
        {
            "actor": [
                {"reference": "Patient/1"},
                {"reference": "Practitioner/30001", "display": "Dr Careful"},
                {"reference": "PractitionerRole/140001"},
                {"reference": "RelatedPerson/9"},
                {"reference": "Device/5"},
                {"reference": "HealthcareService/150001"},
                {"reference": "Location/230001", "type": "Location"},
            ]
        }
    ),
    "logical_and_absolute_actors": _schedule(
        {
            "actor": [
                {"reference": "https://other.example.org/fhir/Device/5"},
                {
                    "identifier": {"system": "urn:device", "value": "D-9"},
                    "display": "Scanner",
                },
            ]
        }
    ),
    "comment": _schedule({"comment": "Weekday clinic"}),
    "extension": _schedule(
        {
            "extension": [
                {
                    "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                    "valueString": "y",
                }
            ]
        }
    ),
    "full_payload": ScheduleModel(
        schedule_id=200001,
        tenant_id="org-test",
        created_by="u-test",
        created_at=D,
        content=_stored(FULL),
    ),
    "minimal_payload": ScheduleModel(
        schedule_id=200001,
        tenant_id="org-test",
        created_by="u-test",
        created_at=D,
        content=_stored(MINIMAL),
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_schedule_mapper_emits_valid_fhir_r4(case):
    assert_valid(schedule_pb2.Schedule, to_fhir_schedule(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = _stored(FULL)
    out = to_fhir_schedule(
        ScheduleModel(
            schedule_id=200001,
            tenant_id="org-test",
            created_by="u-test",
            created_at=D,
            content=content,
        )
    )
    assert out["resourceType"] == "Schedule"
    assert out["id"] == "200001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("active as string not boolean", {"active": "yes"}),
        ("misspelled element", {"planningHorizn": {"start": "2026-01-01"}}),
        ("planningHorizon as string not Period", {"planningHorizon": "2026"}),
        (
            "serviceCategory as strings not CodeableConcepts",
            {"serviceCategory": ["17"]},
        ),
        (
            "specialty as an object not a list",
            {"specialty": {"coding": [{"code": "x"}]}},
        ),
        ("actor as strings not References", {"actor": ["Practitioner/30001"]}),
        ("identifier as strings not Identifiers", {"identifier": ["S-1"]}),
        ("comment as list", {"comment": ["x"]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Schedule", "id": "200001", **MINIMAL, **broken}
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), schedule_pb2.Schedule, validate=True
        )

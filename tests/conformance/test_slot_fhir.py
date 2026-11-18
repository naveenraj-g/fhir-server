"""FHIR R4 conformance for `to_fhir_slot()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Slot is stored Medplum-style (like Schedule and the other content-based
resources): the resource lives whole in SlotModel.content, and to_fhir_slot()
only stamps `id` and `meta` onto it. So what can go wrong on the read side is
that stamping or a stored document the server returns that isn't valid R4 —
each case below is a `content` document as the write path would store it, run
through the real read mapper. (R4 requires `schedule`, `status`, `start` and
`end`, so every case carries them.)
"""

import datetime as dt

import pytest

from app.fhir.mappers.slot import to_fhir_slot
from app.models.slot import SlotModel
from tests.integration.slot.support import full_body, slot_body

from .support import assert_valid, fhir_json_text

slot_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.slot_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
REQUIRED = {
    "schedule": {"reference": "Schedule/200001"},
    "status": "free",
    "start": "2026-06-01T09:00:00Z",
    "end": "2026-06-01T09:30:00Z",
}


def _stored(document: dict) -> dict:
    """What the write path stores: everything but resourceType/id/meta."""
    return {k: v for k, v in document.items() if k not in ("resourceType", "id", "meta")}


def _slot(content: dict, **overrides) -> SlotModel:
    fields = {
        "slot_id": 220001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": {**REQUIRED, **content},
    }
    fields.update(overrides)
    return SlotModel(**fields)


CASES = {
    "minimal": _slot({}),
    **{
        f"status_{s}": _slot({"status": s})
        for s in ("busy", "free", "busy-unavailable", "busy-tentative", "entered-in-error")
    },
    "updated_by_and_updated_at": _slot({}, updated_by="u-other", updated_at=D),
    "start_and_end_with_offset": _slot({"start": "2026-06-01T09:00:00+05:30", "end": "2026-06-01T09:30:00+05:30"}),
    "overbooked_true": _slot({"overbooked": True}),
    "overbooked_false": _slot({"overbooked": False}),
    "comment": _slot({"comment": "Bring previous reports"}),
    "identifier_with_type_and_assigner": _slot(
        {
            "identifier": [
                {
                    "use": "official",
                    "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "SLT"}]},
                    "system": "https://fhir-server.dev/fhir/identifier-system/slot-id",
                    "value": "SL-1",
                    "assigner": {"reference": "Organization/190001"},
                }
            ]
        }
    ),
    "categories_types_and_specialties": _slot(
        {
            "serviceCategory": [{"coding": [{"code": "17", "display": "General Practice"}], "text": "General"}],
            "serviceType": [{"coding": [{"code": "124"}]}, {"text": "Free text only"}],
            "specialty": [{"coding": [{"code": "394579002", "display": "Cardiology"}]}],
        }
    ),
    "appointment_type_single_concept": _slot(
        {"appointmentType": {"coding": [{"code": "ROUTINE", "display": "Routine appointment"}], "text": "Routine"}}
    ),
    "schedule_with_display": _slot({"schedule": {"reference": "Schedule/200001", "display": "Dr Careful clinic"}}),
    "absolute_schedule": _slot({"schedule": {"reference": "https://other.example.org/fhir/Schedule/9"}}),
    "logical_schedule": _slot({"schedule": {"identifier": {"system": "urn:schedules", "value": "SCH-9"}}}),
    "extension": _slot({"extension": [{"url": "https://fhir-server.dev/fhir/StructureDefinition/x", "valueString": "y"}]}),
    "full_payload": SlotModel(
        slot_id=220001, tenant_id="org-test", created_by="u-test", created_at=D, content=_stored(full_body(200001))
    ),
    "minimal_payload": SlotModel(
        slot_id=220001, tenant_id="org-test", created_by="u-test", created_at=D, content=_stored(slot_body(200001))
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_slot_mapper_emits_valid_fhir_r4(case):
    assert_valid(slot_pb2.Slot, to_fhir_slot(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = _stored(full_body(200001))
    out = to_fhir_slot(SlotModel(slot_id=220001, tenant_id="org-test", created_by="u-test", created_at=D, content=content))
    assert out["resourceType"] == "Slot"
    assert out["id"] == "220001"
    assert {k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")} == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — e.g. appointmentType — and an unknown `status`
# code, which the oracle accepts here; the search/core tests cover that.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("status as boolean", {"status": True}),
        ("misspelled element", {"overbookd": True}),
        ("overbooked as string not boolean", {"overbooked": "yes"}),
        ("start not an instant", {"start": "tomorrow"}),
        ("start without a timezone", {"start": "2026-06-01T09:00:00"}),
        ("schedule as string not Reference", {"schedule": "Schedule/200001"}),
        ("serviceCategory as strings not CodeableConcepts", {"serviceCategory": ["17"]}),
        ("specialty as an object not a list", {"specialty": {"coding": [{"code": "x"}]}}),
        ("identifier as strings not Identifiers", {"identifier": ["SL-1"]}),
        ("comment as list", {"comment": ["x"]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Slot", "id": "220001", **REQUIRED, **broken}
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(fhir_json_text(payload), slot_pb2.Slot, validate=True)

"""FHIR R4 conformance for `to_fhir_schedule()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.schedule import to_fhir_schedule
from app.models.schedule import (
    ScheduleActor,
    ScheduleIdentifier,
    ScheduleModel,
    ScheduleServiceCategory,
    ScheduleServiceType,
    ScheduleSpecialty,
)

from .support import assert_valid, fhir_json_text

schedule_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.schedule_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "service_categories",
    "service_types",
    "specialties",
    "actors",
)


def _actor(**kw) -> ScheduleActor:
    return ScheduleActor(
        **{
            "id": 1,
            "org_id": "org-test",
            "reference_type": "Practitioner",
            "reference_id": 30001,
            "reference_display": "Dr. Smith",
            "created_by": "u-test",
            "created_at": D,
            **kw,
        }
    )


def _sched(**overrides) -> ScheduleModel:
    """A Schedule carrying only the columns the model marks NOT NULL, plus
    empty sub-resource lists (nothing is lazy-loadable off a session here).
    A default single `actor` row is always attached unless the caller
    supplies its own `actors` override — FHIR R4 Schedule.actor is 1..*, so
    every shape under test must carry at least one."""
    fields = {
        "schedule_id": 200001,
        "org_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
    }
    fields.update(overrides)
    sched = ScheduleModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(sched, attr, None) is None:
            setattr(sched, attr, [])
    if not sched.actors:
        sched.actors = [_actor()]
    return sched


def _with(attr, *rows) -> ScheduleModel:
    sched = _sched()
    setattr(sched, attr, list(rows))
    return sched


def _identifier(**kw) -> ScheduleIdentifier:
    return ScheduleIdentifier(
        **{
            "id": 1,
            "org_id": "org-test",
            "system": "http://ex.org/sched-ids",
            "value": "SCHED-1",
            "created_by": "u-test",
            "created_at": D,
            **kw,
        }
    )


def _cc(model_cls, **kw):
    return model_cls(
        **{
            "id": 1,
            "org_id": "org-test",
            "coding_system": "http://terminology.hl7.org/CodeSystem/service-category",
            "coding_code": "17",
            "coding_display": "General Practice",
            "created_by": "u-test",
            "created_at": D,
            **kw,
        }
    )


# Each case is one distinct shape the mapper can emit. Anything with a
# conditional branch in app/fhir/mappers/schedule/fhir.py should appear here.
CASES = {
    "minimal": _sched(),

    "active_true": _sched(active=True),
    "active_false": _sched(active=False),

    "comment": _sched(comment="Available for urgent bookings only."),

    "planning_horizon_start_only": _sched(planning_horizon_start=D),
    "planning_horizon_both": _sched(
        planning_horizon_start=D, planning_horizon_end=D
    ),

    "identifier_with_type_and_period": _with(
        "identifiers",
        _identifier(
            use="official",
            type_system="http://terminology.hl7.org/CodeSystem/v2-0203",
            type_version="2.9",
            type_code="PRN",
            type_display="Provider number",
            type_text="Provider number",
            type_user_selected=True,
            period_start=D,
            period_end=D,
        ),
    ),
    "identifier_assigner_resolved": _with(
        "identifiers",
        _identifier(
            assigner_type="Organization", assigner_id=190001, assigner_display="Acme"
        ),
    ),
    "identifier_assigner_fallback": _with(
        "identifiers",
        _identifier(
            assigner_identifier_system="urn:external-registry",
            assigner_identifier_value="EXTERNAL-1",
            assigner_identifier_use="official",
        ),
    ),

    "service_category_with_text": _with(
        "service_categories",
        _cc(ScheduleServiceCategory, text="General Practice"),
    ),
    "service_type_with_text": _with(
        "service_types",
        _cc(
            ScheduleServiceType,
            coding_system="http://example.org/service-type",
            coding_code="57",
            coding_display="Immunization",
            text="Immunization",
            coding_user_selected=True,
        ),
    ),
    "specialty_with_text": _with(
        "specialties",
        _cc(
            ScheduleSpecialty,
            coding_system="http://snomed.info/sct",
            coding_code="394814009",
            coding_display="General practice",
            text="General practice",
        ),
    ),

    "actor_resolved_practitioner": _with(
        "actors",
        _actor(
            reference_type="Practitioner",
            reference_id=30001,
            reference_display="Dr. Smith",
        ),
    ),
    "actor_resolved_location": _with(
        "actors",
        _actor(
            reference_type="Location", reference_id=230001, reference_display="Room 3"
        ),
    ),
    "actor_resolved_device": _with(
        "actors",
        _actor(
            reference_type="Device",
            reference_id=5,
            reference_display="Infusion pump",
        ),
    ),
    "actor_identifier_fallback": _with(
        "actors",
        _actor(
            reference_type=None,
            reference_id=None,
            reference_display=None,
            reference_identifier_system="urn:external-registry",
            reference_identifier_value="EXTERNAL-ACTOR-1",
        ),
    ),
    "actor_multiple": _with(
        "actors",
        _actor(id=1, reference_type="Practitioner", reference_id=30001),
        _actor(id=2, reference_type="Location", reference_id=230001),
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_schedule_mapper_emits_valid_fhir_r4(case):
    assert_valid(schedule_pb2.Schedule, to_fhir_schedule(CASES[case]))


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.

@pytest.mark.parametrize(
    "label,broken",
    [
        ("actor as strings not References", {"actor": ["Practitioner/30001"]}),
        ("misspelled element", {"actor2": [{"reference": "Practitioner/30001"}]}),
        ("active as string not boolean", {"active": "yes"}),
        ("identifier as string not object", {"identifier": ["SCHED-1"]}),
        ("serviceCategory as strings not CodeableConcepts", {"serviceCategory": ["general"]}),
        ("planningHorizon.start not a datetime", {"planningHorizon": {"start": "not-a-date"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "Schedule",
        "id": "200001",
        "actor": [{"reference": "Practitioner/30001"}],
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), schedule_pb2.Schedule, validate=True
        )

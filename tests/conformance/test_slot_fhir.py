"""FHIR R4 conformance for `to_fhir_slot()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.slot import to_fhir_slot
from app.models.slot import (
    SlotIdentifier,
    SlotModel,
    SlotServiceCategory,
    SlotServiceType,
    SlotSpecialty,
)

from .support import assert_valid, fhir_json_text

slot_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.slot_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "service_categories",
    "service_types",
    "specialties",
)


def _slot(**overrides) -> SlotModel:
    """A Slot carrying only the columns the model marks NOT NULL, plus empty
    sub-resource lists (nothing is lazy-loadable off a session here). FHIR R4
    Slot.schedule/status/start/end are all 1..1, so every shape under test
    carries a resolved schedule reference by default unless the caller
    supplies its own schedule_type/schedule_id (or clears them for the
    identifier-fallback shape)."""
    fields = {
        "slot_id": 220001,
        "org_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "schedule_type": "Schedule",
        "schedule_id": 200001,
        "status": "free",
        "start": D,
        "end": D,
    }
    fields.update(overrides)
    slot = SlotModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(slot, attr, None) is None:
            setattr(slot, attr, [])
    return slot


def _with(attr, *rows) -> SlotModel:
    slot = _slot()
    setattr(slot, attr, list(rows))
    return slot


def _identifier(**kw) -> SlotIdentifier:
    return SlotIdentifier(
        **{
            "id": 1,
            "org_id": "org-test",
            "system": "http://ex.org/slot-ids",
            "value": "SLOT-1",
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
# conditional branch in app/fhir/mappers/slot/fhir.py should appear here.
CASES = {
    "minimal": _slot(),

    "status_busy": _slot(status="busy"),
    "status_busy_unavailable": _slot(status="busy-unavailable"),
    "status_busy_tentative": _slot(status="busy-tentative"),
    "status_entered_in_error": _slot(status="entered-in-error"),

    "overbooked_true": _slot(overbooked=True),
    "overbooked_false": _slot(overbooked=False),

    "comment": _slot(comment="Morning slot — first appointment of the day."),

    "schedule_display_only": _slot(schedule_display="Dr. Smith's schedule"),
    "schedule_identifier_fallback": _slot(
        schedule_type=None,
        schedule_id=None,
        schedule_identifier_system="urn:external-registry",
        schedule_identifier_value="EXTERNAL-SCHED-1",
    ),

    "appointment_type": _slot(
        appointment_type_system="http://terminology.hl7.org/CodeSystem/v2-0276",
        appointment_type_code="ROUTINE",
        appointment_type_display="Routine appointment",
    ),
    "appointment_type_with_text": _slot(
        appointment_type_text="Routine appointment",
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
        _cc(SlotServiceCategory, text="General Practice"),
    ),
    "service_type_with_text": _with(
        "service_types",
        _cc(
            SlotServiceType,
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
            SlotSpecialty,
            coding_system="http://snomed.info/sct",
            coding_code="394814009",
            coding_display="General practice",
            text="General practice",
        ),
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_slot_mapper_emits_valid_fhir_r4(case):
    assert_valid(slot_pb2.Slot, to_fhir_slot(CASES[case]))


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.

@pytest.mark.parametrize(
    "label,broken",
    [
        ("schedule as string not Reference", {"schedule": "Schedule/200001"}),
        ("misspelled element", {"schedule2": {"reference": "Schedule/200001"}}),
        ("overbooked as string not boolean", {"overbooked": "yes"}),
        ("identifier as string not object", {"identifier": ["SLOT-1"]}),
        ("serviceCategory as strings not CodeableConcepts", {"serviceCategory": ["general"]}),
        ("start not a datetime", {"start": "not-a-date"}),
        ("status not in the required value set", {"status": "not-a-real-status"}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "Slot",
        "id": "220001",
        "schedule": {"reference": "Schedule/200001"},
        "status": "free",
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), slot_pb2.Slot, validate=True
        )

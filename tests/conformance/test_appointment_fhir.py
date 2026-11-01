"""FHIR R4 conformance for `to_fhir_appointment()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.appointment import to_fhir_appointment
from app.models.appointment import (
    AppointmentAppointmentTypeCoding,
    AppointmentBasedOn,
    AppointmentCancelationReasonCoding,
    AppointmentIdentifier,
    AppointmentIdentifierTypeCoding,
    AppointmentModel,
    AppointmentParticipant,
    AppointmentParticipantType,
    AppointmentParticipantTypeCoding,
    AppointmentReasonCode,
    AppointmentReasonCodeCoding,
    AppointmentReasonReference,
    AppointmentRequestedPeriod,
    AppointmentServiceCategory,
    AppointmentServiceCategoryCoding,
    AppointmentServiceType,
    AppointmentServiceTypeCoding,
    AppointmentSlot,
    AppointmentSpecialty,
    AppointmentSpecialtyCoding,
    AppointmentStatus,
    AppointmentSupportingInformation,
)
from app.models.appointment.enums import (
    AppointmentParticipantRequired,
    AppointmentParticipationStatus,
)

from .support import assert_valid, fhir_json_text

appointment_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.appointment_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 9, 0, tzinfo=dt.timezone.utc)
D2 = dt.datetime(2026, 1, 1, 9, 30, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "service_categories",
    "service_types",
    "specialties",
    "reason_codes",
    "reason_references",
    "supporting_informations",
    "slots",
    "based_ons",
    "participants",
    "requested_periods",
    "cancelation_reason_codings",
    "appointment_type_codings",
)


def _participant(**overrides) -> AppointmentParticipant:
    fields = {
        "id": 1,
        "tenant_id": "org-test",
        "status": AppointmentParticipationStatus.accepted,
        "required": AppointmentParticipantRequired.required,
        "actor_type": "Practitioner",
        "actor_id": 30001,
        "actor_display": "Dr. Smith",
        "created_by": "u-test",
        "created_at": D,
    }
    fields.update(overrides)
    p = AppointmentParticipant(**fields)
    p.types = []
    return p


def _appt(**overrides) -> AppointmentModel:
    """An Appointment carrying NOT NULL columns + required participant."""
    fields = {
        "appointment_id": 40001,
        "tenant_id": "org-test",
        "status": AppointmentStatus.booked,
        "start": D,
        "end": D2,
        "created_by": "u-test",
        "created_at": D,
    }
    fields.update(overrides)
    appt = AppointmentModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(appt, attr, None) is None:
            setattr(appt, attr, [])
    if not appt.participants:
        appt.participants = [_participant()]
    return appt


def _with(attr, *rows) -> AppointmentModel:
    appt = _appt()
    setattr(appt, attr, list(rows))
    return appt


def _identifier(**kw) -> AppointmentIdentifier:
    defaults = {
        "id": 1,
        "tenant_id": "org-test",
        "system": "http://example.org/appointment",
        "value": "APP-1",
        "created_by": "u-test",
        "created_at": D,
    }
    defaults.update(kw)
    type_codings = defaults.pop("type_codings", [])
    ident = AppointmentIdentifier(**defaults)
    ident.type_codings = type_codings
    return ident


CASES = {
    "minimal": _appt(),
    "status_proposed": _appt(status=AppointmentStatus.proposed),
    "status_cancelled": _appt(
        status=AppointmentStatus.cancelled,
        cancelation_reason_text="Patient cancelled",
    ),
    "description_and_comment": _appt(
        description="Routine checkup",
        comment="Please arrive 10 min early",
        patient_instruction="Fast for 12 hours",
        priority=1,
        minutes_duration=30,
    ),
    "identifier_with_assigner_resolved": _with(
        "identifiers",
        _identifier(
            assigner_type="Organization",
            assigner_id=190001,
            assigner_display="Acme Clinic",
        ),
    ),
    "identifier_with_assigner_fallback": _with(
        "identifiers",
        _identifier(
            assigner_identifier_system="http://external-assigner.example.org",
            assigner_identifier_value="EXT-ORG-1",
            assigner_identifier_use="official",
        ),
    ),
    "participant_actor_fallback": _appt(
        participants=[
            _participant(
                actor_type=None,
                actor_id=None,
                actor_display="External Participant",
                actor_identifier_system="http://patients.example.org",
                actor_identifier_value="EXT-PAT-123",
                actor_identifier_use="official",
            )
        ]
    ),
    "reason_reference_with_fallback": _with(
        "reason_references",
        AppointmentReasonReference(
            id=1,
            tenant_id="org-test",
            reference_display="External Condition",
            reference_identifier_system="http://conditions.example.org",
            reference_identifier_value="COND-999",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "supporting_information_with_fallback": _with(
        "supporting_informations",
        AppointmentSupportingInformation(
            id=1,
            tenant_id="org-test",
            reference_display="External Lab Result",
            reference_identifier_system="http://labs.example.org",
            reference_identifier_value="LAB-DOC-55",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "slot_with_reference": _with(
        "slots",
        AppointmentSlot(
            id=1,
            tenant_id="org-test",
            reference_type="Slot",
            reference_id=220001,
            reference_display="Slot 220001",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "based_on_with_fallback": _with(
        "based_ons",
        AppointmentBasedOn(
            id=1,
            tenant_id="org-test",
            reference_display="External Referral",
            reference_identifier_system="http://referrals.example.org",
            reference_identifier_value="REF-777",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "requested_period": _with(
        "requested_periods",
        AppointmentRequestedPeriod(
            id=1,
            tenant_id="org-test",
            start=D,
            end=D2,
            created_by="u-test",
            created_at=D,
        ),
    ),
}


@pytest.mark.parametrize("case_name", list(CASES.keys()))
def test_appointment_fhir_conformance(case_name: str):
    model = CASES[case_name]
    output = to_fhir_appointment(model)
    assert_valid(appointment_pb2.Appointment, output)

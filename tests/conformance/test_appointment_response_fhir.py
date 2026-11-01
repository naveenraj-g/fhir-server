"""FHIR R4 conformance for `to_fhir_appointment_response()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.appointment_response import to_fhir_appointment_response
from app.models.appointment_response import (
    AppointmentResponseIdentifier,
    AppointmentResponseIdentifierTypeCoding,
    AppointmentResponseModel,
    AppointmentResponseParticipantType,
    AppointmentResponseParticipantTypeCoding,
)
from app.models.appointment_response.enums import (
    AppointmentResponseParticipantStatus,
)

from .support import assert_valid, fhir_json_text

appointment_response_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.appointment_response_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 9, 0, tzinfo=dt.timezone.utc)
D2 = dt.datetime(2026, 1, 1, 9, 30, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "participant_types",
)


def _resp(**overrides) -> AppointmentResponseModel:
    """An AppointmentResponse carrying NOT NULL columns + required appointment/participantStatus/actor."""
    fields = {
        "appointment_response_id": 370001,
        "tenant_id": "org-test",
        "appointment_type": "Appointment",
        "appointment_id": 40001,
        "appointment_display": "Dr. Smith consultation",
        "participant_status": AppointmentResponseParticipantStatus.accepted,
        "actor_type": "Practitioner",
        "actor_id": 30001,
        "actor_display": "Dr. Smith",
        "start": D,
        "end": D2,
        "created_by": "u-test",
        "created_at": D,
    }
    fields.update(overrides)
    resp = AppointmentResponseModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(resp, attr, None) is None:
            setattr(resp, attr, [])
    return resp


def _with(attr, *rows) -> AppointmentResponseModel:
    resp = _resp()
    setattr(resp, attr, list(rows))
    return resp


def _identifier(**kw) -> AppointmentResponseIdentifier:
    defaults = {
        "id": 1,
        "tenant_id": "org-test",
        "system": "http://example.org/appointment-response",
        "value": "RESP-1",
        "created_by": "u-test",
        "created_at": D,
    }
    defaults.update(kw)
    type_codings = defaults.pop("type_codings", [])
    ident = AppointmentResponseIdentifier(**defaults)
    ident.type_codings = type_codings
    return ident


CASES = {
    "minimal": _resp(),
    "status_declined": _resp(
        participant_status=AppointmentResponseParticipantStatus.declined,
        comment="Conflict with another surgery",
    ),
    "status_tentative": _resp(
        participant_status=AppointmentResponseParticipantStatus.tentative,
    ),
    "status_needs_action": _resp(
        participant_status=AppointmentResponseParticipantStatus.needs_action,
    ),
    "appointment_with_identifier_fallback": _resp(
        appointment_type=None,
        appointment_id=None,
        appointment_identifier_system="http://appointments.example.org",
        appointment_identifier_value="EXT-APP-888",
        appointment_identifier_use="official",
    ),
    "actor_with_identifier_fallback": _resp(
        actor_type=None,
        actor_id=None,
        actor_display="External Attendee",
        actor_identifier_system="http://external-practitioners.example.org",
        actor_identifier_value="NPI-998877",
        actor_identifier_use="official",
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
            assigner_identifier_value="EXT-ORG-RESP",
            assigner_identifier_use="official",
        ),
    ),
    "participant_type": _with(
        "participant_types",
        AppointmentResponseParticipantType(
            id=1,
            tenant_id="org-test",
            text="attender",
            codings=[
                AppointmentResponseParticipantTypeCoding(
                    id=1,
                    system="http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                    code="ATND",
                    display="attender",
                    created_by="u-test",
                    created_at=D,
                )
            ],
            created_by="u-test",
            created_at=D,
        ),
    ),
}


@pytest.mark.parametrize("case_name", list(CASES.keys()))
def test_appointment_response_fhir_conformance(case_name: str):
    model = CASES[case_name]
    output = to_fhir_appointment_response(model)
    assert_valid(appointment_response_pb2.AppointmentResponse, output)

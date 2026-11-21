"""
FHIR AppointmentResponse document -> search index. The only write-side mapper.

An AppointmentResponse is stored whole, verbatim, in
AppointmentResponseModel.content; this module derives every *other* column and
child row from it — exactly the values the FHIR R4 AppointmentResponse search
parameters filter on
(https://www.hl7.org/fhir/R4/appointmentresponse.html#search), nothing more.
See AppointmentResponseModel's docstring for the parameter -> storage table;
the shared builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from app.models.appointment_response import (
    AppointmentResponseIdentifier,
    AppointmentResponseParticipantStatus,
)
from app.repository._content_index import identifier_rows, relative

from ._shared import MODELED_ACTOR_TYPES, actor_type_and_id, appointment_id_of

# Relationship attributes the index owns — every one is rebuilt on each write.
INDEX_RELATIONSHIPS = ("identifiers",)


def local_references(document: dict) -> list[tuple[str, str, str]]:
    """(element label, resource type, relative reference) for every local
    reference that must exist in the caller's org on write: identifier.assigner,
    `appointment`, and an `actor` of a type this server models. Absolute URLs,
    logical (identifier-only) references and an actor of a type that is not a
    resource here (RelatedPerson, Device) point elsewhere and are not checked."""
    refs = []
    for identifier in document.get("identifier") or []:
        local = relative(
            (identifier.get("assigner") or {}).get("reference"), "Organization"
        )
        if local:
            refs.append(("identifier.assigner", "Organization", local))
    appointment = relative(
        (document.get("appointment") or {}).get("reference"), "Appointment"
    )
    if appointment:
        refs.append(("appointment", "Appointment", appointment))
    actor = (document.get("actor") or {}).get("reference")
    parsed = actor_type_and_id(actor)
    if parsed and parsed[0] in MODELED_ACTOR_TYPES:
        refs.append(("actor", parsed[0], actor))
    return refs


def _reference_columns(
    prefix: str, ref: dict | None, parsed: tuple[str, int] | None
) -> dict:
    ref = ref or {}
    identifier = ref.get("identifier") or {}
    return {
        f"{prefix}_reference": ref.get("reference"),
        f"{prefix}_type": parsed[0] if parsed else None,
        f"{prefix}_id": parsed[1] if parsed else None,
        f"{prefix}_identifier_system": identifier.get("system"),
        f"{prefix}_identifier_value": identifier.get("value"),
    }


def index_columns(document: dict) -> dict:
    """Search columns on the appointment_response row itself."""
    status = document.get("participantStatus")
    try:
        status = AppointmentResponseParticipantStatus(status) if status else None
    except ValueError:
        status = None  # the validator rejects a bad code before we get here
    appointment = document.get("appointment") or {}
    appointment_id = appointment_id_of(appointment.get("reference"))
    actor = document.get("actor") or {}
    return {
        "participant_status": status,
        **_reference_columns(
            "appointment",
            appointment,
            ("Appointment", appointment_id) if appointment_id is not None else None,
        ),
        **_reference_columns("actor", actor, actor_type_and_id(actor.get("reference"))),
    }


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by AppointmentResponseModel relationship name."""
    return {
        "identifiers": [
            r
            for i in document.get("identifier") or []
            for r in identifier_rows(AppointmentResponseIdentifier, i)
        ],
    }

"""
FHIR Appointment document -> search index. The only write-side mapper.

Appointment's whole resource is stored verbatim in AppointmentModel.content;
this module derives every *other* column and child row from it — exactly the
values the FHIR R4 Appointment search parameters filter on
(https://www.hl7.org/fhir/R4/appointment.html#search), nothing more. See
AppointmentModel's docstring for the parameter -> storage table; the shared
builders are in app.repository._content_index.

Works on the plain FHIR JSON dict (the validated document that is also
stored), so create and patch share one path: both hand over the full
post-write document.
"""

from __future__ import annotations

from datetime import UTC, datetime
from functools import partial

from app.fhir.search.values import parse_date
from app.models.appointment import (
    REFERENCE_PARAMS,
    TOKEN_PARAMS,
    AppointmentIdentifier,
    AppointmentParticipant,
    AppointmentReference,
    AppointmentStatus,
    AppointmentToken,
)
from app.repository._content_index import identifier_rows, relative, type_rows

from ._shared import MODELED_ACTOR_TYPES, actor_type_and_id, ref_type_and_id

# Relationship attributes the index owns — every one is rebuilt on each write.
INDEX_RELATIONSHIPS = ("identifiers", "tokens", "references", "participants")


def local_references(document: dict) -> list[tuple[str, str, str]]:
    """(element label, resource type, relative reference) for every local
    reference that must exist in the caller's org on write: identifier.assigner,
    every Slot in `slot`, and every participant actor of a type this server
    models. Absolute URLs, logical (identifier-only) references and actors of
    a type that isn't a resource here (RelatedPerson, Device) point elsewhere
    and aren't checked; neither are basedOn / reasonReference /
    supportingInformation, which target resources this server doesn't rebuild."""
    refs = []
    for identifier in document.get("identifier") or []:
        local = relative((identifier.get("assigner") or {}).get("reference"), "Organization")
        if local:
            refs.append(("identifier.assigner", "Organization", local))
    for slot in document.get("slot") or []:
        local = relative(slot.get("reference"), "Slot")
        if local:
            refs.append(("slot", "Slot", local))
    for reason in document.get("reasonReference") or []:
        for resource_type in ("Condition", "Procedure"):
            local = relative(reason.get("reference"), resource_type)
            if local:
                refs.append(("reasonReference", resource_type, local))
    for participant in document.get("participant") or []:
        actor = participant.get("actor") or {}
        parsed = actor_type_and_id(actor.get("reference"))
        if parsed and parsed[0] in MODELED_ACTOR_TYPES:
            refs.append(("participant.actor", parsed[0], actor["reference"]))
    return refs


def _instant(value) -> datetime | None:
    """Appointment.start as a UTC datetime (None if absent or unparseable — a
    bad instant is the validator's to reject)."""
    if not value:
        return None
    try:
        return parse_date(str(value)).low.astimezone(UTC)
    except Exception:
        return None


def index_columns(document: dict) -> dict:
    """Search columns on the appointment row itself."""
    status = document.get("status")
    try:
        status = AppointmentStatus(status) if status else None
    except ValueError:
        status = None  # the validator rejects a bad code before we get here
    return {"status": status, "start": _instant(document.get("start"))}


def _concepts(value) -> list[dict]:
    """A CodeableConcept element as a list: `appointmentType` is 0..1 (an
    object), the others 0..* (a list)."""
    if isinstance(value, dict):
        return [value]
    return list(value or [])


def _reference_row(param: str, ref: dict | None) -> AppointmentReference | None:
    """One index row for a Reference with a `reference` or an `identifier`
    (display-only can't be matched by a reference search)."""
    ref = ref or {}
    reference = ref.get("reference")
    identifier = ref.get("identifier") or {}
    if not (reference or identifier.get("value")):
        return None
    parsed = ref_type_and_id(reference, param)
    return AppointmentReference(
        param=param,
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
    )


def _participant_row(participant: dict) -> AppointmentParticipant:
    """One row per participant, even one with no actor (for `part-status`)."""
    actor = participant.get("actor") or {}
    reference = actor.get("reference")
    identifier = actor.get("identifier") or {}
    parsed = actor_type_and_id(reference)
    return AppointmentParticipant(
        reference_reference=reference,
        reference_type=parsed[0] if parsed else None,
        reference_id=parsed[1] if parsed else None,
        reference_identifier_system=identifier.get("system"),
        reference_identifier_value=identifier.get("value"),
        status=participant.get("status"),
    )


def index_rows(document: dict) -> dict[str, list]:
    """Child index rows, keyed by AppointmentModel relationship name."""
    tokens = []
    for param, element in TOKEN_PARAMS.items():
        model = partial(AppointmentToken, param=param)
        for concept in _concepts(document.get(element)):
            tokens.extend(type_rows(model, concept))
    references = []
    for param, element in REFERENCE_PARAMS.items():
        references += [r for ref in document.get(element) or [] if (r := _reference_row(param, ref))]
    return {
        "identifiers": [
            r for i in document.get("identifier") or [] for r in identifier_rows(AppointmentIdentifier, i)
        ],
        "tokens": tokens,
        "references": references,
        "participants": [_participant_row(p) for p in document.get("participant") or []],
    }

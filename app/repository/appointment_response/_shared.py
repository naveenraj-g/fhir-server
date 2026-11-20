import re

from sqlalchemy.orm import selectinload

from app.models.appointment_response import ACTOR_TYPES, AppointmentResponseModel
from app.repository._reference_shared import _validate_reference

__all__ = [
    "MODELED_ACTOR_TYPES",
    "_validate_reference",
    "_with_relationships",
    "actor_type_and_id",
    "appointment_id_of",
]

# Of the seven AppointmentResponse.actor target types, these are resources on
# this server (registered in RESOURCE_REGISTRY — see
# app/core/reference_resolver.py). A relative RelatedPerson/Device reference is
# accepted and indexed but not existence-checked: ensure_resource_exists()
# fails closed for an unregistered type (422 on every valid reference to one).
MODELED_ACTOR_TYPES = {"Patient", "Practitioner", "PractitionerRole", "HealthcareService", "Location"}

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")


def _with_relationships(stmt):
    """Eager-load the search-index child rows. Only needed when a write is
    about to replace them (patch_full) — reads never touch them, since every
    response is served straight from AppointmentResponseModel.content."""
    return stmt.options(selectinload(AppointmentResponseModel.identifiers))


def _split(reference: str | None) -> tuple[str, int] | None:
    match = _REF.match(reference or "")
    return (match["type"], int(match["id"])) if match else None


def actor_type_and_id(reference: str | None) -> tuple[str, int] | None:
    """('Practitioner', 30001) for a relative `Type/<id>` naming one of the
    seven allowed actor types; None for an absolute URL, a contained reference
    or any other shape (those match by their raw string only)."""
    parsed = _split(reference)
    return parsed if parsed and parsed[0] in ACTOR_TYPES else None


def appointment_id_of(reference: str | None) -> int | None:
    """The public id of a relative `Appointment/<id>` reference; None for any
    other shape."""
    parsed = _split(reference)
    return parsed[1] if parsed and parsed[0] == "Appointment" else None

import re

from sqlalchemy.orm import selectinload

from app.models.appointment import ACTOR_TYPES, REFERENCE_TYPES, AppointmentModel
from app.repository._reference_shared import _validate_reference

__all__ = [
    "MODELED_ACTOR_TYPES",
    "_validate_reference",
    "_with_relationships",
    "actor_type_and_id",
    "ref_type_and_id",
]

# Of the seven Appointment.participant.actor target types, these are resources
# on this server (registered in RESOURCE_REGISTRY — see
# app/core/reference_resolver.py). A relative Device reference is
# accepted and indexed but not existence-checked: ensure_resource_exists()
# fails closed for an unregistered type (422 on every valid reference to one).
MODELED_ACTOR_TYPES = {"Patient", "Practitioner", "PractitionerRole", "RelatedPerson", "HealthcareService", "Location"}

_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")


def _with_relationships(stmt):
    """Eager-load the search-index child rows. Only needed when a write is
    about to replace them (patch_full) — reads never touch them, since every
    response is served straight from AppointmentModel.content."""
    return stmt.options(
        *(selectinload(getattr(AppointmentModel, rel)) for rel in ("identifiers", "tokens", "references", "participants"))
    )


def _split(reference: str | None) -> tuple[str, int] | None:
    match = _REF.match(reference or "")
    return (match["type"], int(match["id"])) if match else None


def actor_type_and_id(reference: str | None) -> tuple[str, int] | None:
    """('Practitioner', 30001) for a relative `Type/<id>` naming one of the
    seven allowed actor types; None for an absolute URL, a contained reference
    or any other shape (those match by their raw string only)."""
    parsed = _split(reference)
    return parsed if parsed and parsed[0] in ACTOR_TYPES else None


def ref_type_and_id(reference: str | None, param: str) -> tuple[str, int] | None:
    """('Slot', 220001) for a relative `Type/<id>` naming a type the search
    parameter `param` (based-on | reason-reference | slot | supporting-info)
    allows; None for an absolute URL, a contained reference or any other shape
    (those match by their raw string only). supporting-info is Reference(Any),
    so any type is accepted there."""
    parsed = _split(reference)
    if not parsed:
        return None
    allowed = REFERENCE_TYPES[param]
    return parsed if allowed is None or parsed[0] in allowed else None

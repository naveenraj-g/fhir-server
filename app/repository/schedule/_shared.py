import re

from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.schedule import ScheduleActorReferenceType, ScheduleModel
from app.repository._reference_shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _org_ref_kwargs,
    _parse_org_ref,
    _reference_kwargs,
    _validate_reference,
)

__all__ = [
    "ACTOR_TYPES",
    "MODELED_ACTOR_TYPES",
    "_IDENTIFIER_FALLBACK_SUFFIXES",
    "_org_ref_kwargs",
    "_parse_actor_ref",
    "_parse_org_ref",
    "_reference_kwargs",
    "_validate_actor_reference",
    "_validate_reference",
    "_with_relationships",
    "actor_type_and_id",
]

# FHIR R4's seven allowed Schedule.actor target types.
ACTOR_TYPES = tuple(t.value for t in ScheduleActorReferenceType)

# Of those, only these four are resources on this server (registered in
# RESOURCE_REGISTRY — see app/core/reference_resolver.py). A relative
# Patient/RelatedPerson/Device reference is accepted and indexed but not
# existence-checked: calling ensure_resource_exists() for an unregistered type
# fails closed (422 on every valid reference to one).
MODELED_ACTOR_TYPES = {
    "Practitioner",
    "PractitionerRole",
    "HealthcareService",
    "Location",
}

_ACTOR_REF = re.compile(r"^(?P<type>[A-Za-z]+)/(?P<id>\d+)$")


def _with_relationships(stmt):
    """Eager-load the search-index child rows. Only needed when a write is
    about to replace them (patch_full) — reads never touch them, since every
    response is served straight from ScheduleModel.content."""
    return stmt.options(
        *(
            selectinload(getattr(ScheduleModel, rel))
            for rel in ("identifiers", "tokens", "actors")
        )
    )


def actor_type_and_id(reference: str | None) -> tuple[str, int] | None:
    """('Practitioner', 30001) for a relative `Type/<id>` naming one of the
    seven allowed actor types; None for an absolute URL, a contained reference
    or any other shape (those match by their raw string only)."""
    match = _ACTOR_REF.match(reference or "")
    if match and match["type"] in ACTOR_TYPES:
        return match["type"], int(match["id"])
    return None


def _parse_actor_ref(ref: str) -> tuple:
    """Parse 'Practitioner/30001' → (ScheduleActorReferenceType.Practitioner, 30001)."""
    return parse_reference(ref, ScheduleActorReferenceType)


async def _validate_actor_reference(session, org_id, ref_type, ref_id) -> None:
    """Existence-check a Schedule.actor reference — but only for the four
    target types this server models (see MODELED_ACTOR_TYPES)."""
    if getattr(ref_type, "value", ref_type) in MODELED_ACTOR_TYPES:
        await _validate_reference(session, org_id, ref_type, ref_id, "actor")

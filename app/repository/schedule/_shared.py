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
    "_IDENTIFIER_FALLBACK_SUFFIXES",
    "_SORTABLE_FIELDS",
    "_actor_ref_kwargs",
    "_org_ref_kwargs",
    "_parse_actor_ref",
    "_parse_org_ref",
    "_reference_kwargs",
    "_validate_actor_reference",
    "_validate_reference",
    "_with_relationships",
]


# Sortable fields exposed via the `sort` list-query param (see
# app.core.pagination.resolve_sort) — mirrors HealthcareService's _shared.py.
_SORTABLE_FIELDS = {
    "schedule_id": ScheduleModel.schedule_id,
    "created_at": ScheduleModel.created_at,
    "updated_at": ScheduleModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load all 5 schedule sub-resources to avoid N+1 and async
    lazy-load failures."""
    return stmt.options(
        selectinload(ScheduleModel.identifiers),
        selectinload(ScheduleModel.service_categories),
        selectinload(ScheduleModel.service_types),
        selectinload(ScheduleModel.specialties),
        selectinload(ScheduleModel.actors),
    )


def _parse_actor_ref(ref: str) -> tuple:
    """Parse 'Practitioner/30001' → (ScheduleActorReferenceType.Practitioner, 30001).
    Unlike HealthcareService's per-list-fixed-type references, Schedule.actor
    is genuinely polymorphic per item — one shared enum covers all seven
    allowed target types, so a single parse function (rather than one per
    reference-type family) is enough."""
    return parse_reference(ref, ScheduleActorReferenceType)


def _actor_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM constructor
    kwargs from a FHIR reference string (e.g. 'Practitioner/30001') for the
    Schedule.actor[] polymorphic Reference field."""
    ref_type, ref_id = _parse_actor_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


async def _validate_actor_reference(session, org_id, ref_type, ref_id, field_name: str) -> None:
    """Same as the shared `_validate_reference`, except a Device-typed actor
    reference is always accepted with no existence check — Device isn't a
    modeled resource in this codebase (no RESOURCE_REGISTRY entry), so
    checking it would fail closed and reject every valid Device actor. Same
    treatment HealthcareService gives its unmodeled Endpoint target."""
    if ref_type == ScheduleActorReferenceType.Device:
        return
    await _validate_reference(session, org_id, ref_type, ref_id, field_name)

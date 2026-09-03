from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.slot import SlotModel
from app.models.slot.enums import SlotScheduleReferenceType
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
    "_org_ref_kwargs",
    "_parse_org_ref",
    "_parse_schedule_ref",
    "_reference_kwargs",
    "_schedule_ref_kwargs",
    "_validate_reference",
    "_with_relationships",
]


# Sortable fields exposed via the `sort` list-query param (see
# app.core.pagination.resolve_sort) — mirrors Schedule's _shared.py.
_SORTABLE_FIELDS = {
    "slot_id": SlotModel.slot_id,
    "start": SlotModel.start,
    "end": SlotModel.end,
    "created_at": SlotModel.created_at,
    "updated_at": SlotModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load all 4 slot sub-resources to avoid N+1 and async lazy-load
    failures."""
    return stmt.options(
        selectinload(SlotModel.identifiers),
        selectinload(SlotModel.service_categories),
        selectinload(SlotModel.service_types),
        selectinload(SlotModel.specialties),
    )


def _parse_schedule_ref(ref: str) -> tuple:
    """Parse 'Schedule/200001' → (SlotScheduleReferenceType.Schedule, 200001).
    SlotScheduleReferenceType only has one member (Schedule.schedule is 1..1
    and can only ever point at a Schedule), but a dedicated parse function is
    kept for symmetry with every other flattened-reference field in this
    codebase, and so a bad type prefix still 422s with a clear message
    instead of silently mismatching."""
    return parse_reference(ref, SlotScheduleReferenceType)


def _schedule_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM constructor
    kwargs from a FHIR reference string (e.g. 'Schedule/200001') for the
    Slot.schedule (1..1) Reference field."""
    ref_type, ref_id = _parse_schedule_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }

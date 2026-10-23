from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.enums import ScheduleReferenceType
from app.models.slot import (
    SlotIdentifier,
    SlotModel,
    SlotServiceCategory,
    SlotServiceType,
    SlotSpecialty,
)
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
    """Eager-load all 5 slot sub-resources to avoid N+1 and async
    lazy-load failures. identifier.type_codings, service_category.codings,
    service_type.codings, and specialty.codings are each a nested 0..*
    coding child table now (see app.models.slot.*) — mirrors
    app.repository.schedule._shared._with_relationships."""
    return stmt.options(
        selectinload(SlotModel.identifiers).selectinload(
            SlotIdentifier.type_codings
        ),
        selectinload(SlotModel.service_categories).selectinload(
            SlotServiceCategory.codings
        ),
        selectinload(SlotModel.service_types).selectinload(
            SlotServiceType.codings
        ),
        selectinload(SlotModel.specialties).selectinload(SlotSpecialty.codings),
        selectinload(SlotModel.appointment_type_codings),
    )


def _parse_schedule_ref(ref: str) -> tuple:
    """Parse 'Schedule/200001' → (ScheduleReferenceType.Schedule, 200001)."""
    return parse_reference(ref, ScheduleReferenceType)


def _schedule_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM constructor
    kwargs from a FHIR reference string (e.g. 'Schedule/200001') for
    Slot.schedule."""
    ref_type, ref_id = _parse_schedule_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }

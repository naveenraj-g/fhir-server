from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.enums import ScheduleReferenceType
from app.models.slot import SlotModel
from app.repository._reference_shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _org_ref_kwargs,
    _parse_org_ref,
    _reference_kwargs,
    _validate_reference,
)

__all__ = [
    "_IDENTIFIER_FALLBACK_SUFFIXES",
    "_org_ref_kwargs",
    "_parse_org_ref",
    "_parse_schedule_ref",
    "_reference_kwargs",
    "_validate_reference",
    "_with_relationships",
]


def _with_relationships(stmt):
    """Eager-load the search-index child rows. Only needed when a write is
    about to replace them (patch_full) — reads never touch them, since every
    response is served straight from SlotModel.content."""
    return stmt.options(
        *(selectinload(getattr(SlotModel, rel)) for rel in ("identifiers", "tokens"))
    )


def _parse_schedule_ref(ref: str) -> tuple:
    """Parse 'Schedule/200001' → (ScheduleReferenceType.Schedule, 200001)."""
    return parse_reference(ref, ScheduleReferenceType)

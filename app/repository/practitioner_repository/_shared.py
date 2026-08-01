from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.practitioner import PractitionerModel, PractitionerQualification
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
    "_reference_kwargs",
    "_validate_reference",
    "_with_relationships",
    "_delete_child",
    "_fetch_child",
    "_SORTABLE_FIELDS",
]


# Sortable fields exposed via the `sort` list-query param (see
# app.core.pagination.resolve_sort) — mirrors Patient's _shared.py exactly.
_SORTABLE_FIELDS = {
    "practitioner_id": PractitionerModel.practitioner_id,
    "birth_date": PractitionerModel.birth_date,
    "created_at": PractitionerModel.created_at,
    "updated_at": PractitionerModel.updated_at,
    "gender": PractitionerModel.gender,
}


def _with_relationships(stmt):
    """Eager-load all practitioner sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(PractitionerModel.names),
        selectinload(PractitionerModel.identifiers),
        selectinload(PractitionerModel.telecoms),
        selectinload(PractitionerModel.addresses),
        selectinload(PractitionerModel.photos),
        selectinload(PractitionerModel.qualifications).selectinload(PractitionerQualification.identifiers),
        selectinload(PractitionerModel.communications),
    )


async def _delete_child(session, model_class, child_id: int, parent_internal_id: int) -> bool:
    """Delete a child row by its id, verifying it belongs to the given parent internal id."""
    row = (await session.execute(
        select(model_class).where(model_class.id == child_id)
    )).scalars().first()
    if not row or row.practitioner_id != parent_internal_id:
        return False
    await session.delete(row)
    await session.commit()
    return True


async def _fetch_child(session, model_class, child_id: int, parent_internal_id: int):
    """Fetch child by id, verify parent ownership, return row or None."""
    row = (await session.execute(
        select(model_class).where(model_class.id == child_id)
    )).scalars().first()
    if not row or row.practitioner_id != parent_internal_id:
        return None
    return row

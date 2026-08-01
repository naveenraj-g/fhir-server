from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.patient.patient import PatientContact, PatientModel
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
]


# Sortable fields exposed via the `sort` list-query param (see
# app.core.pagination.resolve_sort) — only first-class PatientModel columns
# are sortable for now; sorting by a child-table field (e.g. family name)
# would need a join rather than the EXISTS-subquery pattern this package uses
# for filtering, and hasn't been needed yet.
_SORTABLE_FIELDS = {
    "patient_id": PatientModel.patient_id,
    "birth_date": PatientModel.birth_date,
    "created_at": PatientModel.created_at,
    "updated_at": PatientModel.updated_at,
    "gender": PatientModel.gender,
}


def _with_relationships(stmt):
    return stmt.options(
        selectinload(PatientModel.names),
        selectinload(PatientModel.identifiers),
        selectinload(PatientModel.telecoms),
        selectinload(PatientModel.addresses),
        selectinload(PatientModel.photos),
        selectinload(PatientModel.contacts).selectinload(PatientContact.relationships),
        selectinload(PatientModel.contacts).selectinload(PatientContact.telecoms),
        selectinload(PatientModel.communications),
        selectinload(PatientModel.general_practitioners),
        selectinload(PatientModel.links),
    )


async def _delete_child(session, model_class, child_id: int, parent_internal_id: int) -> bool:
    """Delete a child row by its id, verifying it belongs to the given parent internal id."""
    result = await session.execute(
        select(model_class).where(
            model_class.id == child_id,
            model_class.patient_id == parent_internal_id,
        )
    )
    row = result.scalars().first()
    if not row:
        return False
    try:
        await session.delete(row)
        await session.commit()
        return True
    except Exception:
        await session.rollback()
        raise


async def _fetch_child(session, model_class, child_id: int, parent_internal_id: int):
    """Fetch child by id, verify parent ownership, return row or None."""
    result = await session.execute(
        select(model_class).where(
            model_class.id == child_id,
            model_class.patient_id == parent_internal_id,
        )
    )
    return result.scalars().first()

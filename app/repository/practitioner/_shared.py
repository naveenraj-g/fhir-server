from sqlalchemy.orm import selectinload

from app.models.practitioner import (
    PractitionerCommunication,
    PractitionerIdentifier,
    PractitionerModel,
    PractitionerQualification,
    PractitionerQualificationIdentifier,
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
    "_reference_kwargs",
    "_validate_reference",
    "_with_relationships",
]


# Sortable fields exposed via the `sort` list-query param (see
# app.core.pagination.resolve_sort) — mirrors Organization's _shared.py.
_SORTABLE_FIELDS = {
    "practitioner_id": PractitionerModel.practitioner_id,
    "created_at": PractitionerModel.created_at,
    "updated_at": PractitionerModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load all Practitioner sub-resources to avoid N+1 and async
    lazy-load failures."""
    return stmt.options(
        selectinload(PractitionerModel.identifiers).selectinload(
            PractitionerIdentifier.type_codings
        ),
        selectinload(PractitionerModel.names),
        selectinload(PractitionerModel.telecoms),
        selectinload(PractitionerModel.addresses),
        selectinload(PractitionerModel.photos),
        selectinload(PractitionerModel.qualifications).selectinload(
            PractitionerQualification.code_codings
        ),
        selectinload(PractitionerModel.qualifications)
        .selectinload(PractitionerQualification.identifiers)
        .selectinload(PractitionerQualificationIdentifier.type_codings),
        selectinload(PractitionerModel.communications).selectinload(
            PractitionerCommunication.codings
        ),
    )

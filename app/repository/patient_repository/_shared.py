from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import ensure_resource_exists
from app.models.enums import OrganizationReferenceType
from app.models.patient.patient import PatientContact, PatientModel


def _parse_org_ref(ref: str) -> tuple:
    """
    Parse 'Organization/123' → (OrganizationReferenceType.Organization, 123).

    Delegates to the shared app.core.filters.parse_reference — kept as a thin,
    name-stable wrapper here so every existing call site in this package
    (create/create_full/patch/patch_full, and the Contact sub-resource
    mutations) needed zero changes when the parsing logic was generalized.
    """
    return parse_reference(ref, OrganizationReferenceType)


_IDENTIFIER_FALLBACK_SUFFIXES = (
    "identifier_use",
    "identifier_type_system",
    "identifier_type_version",
    "identifier_type_code",
    "identifier_type_display",
    "identifier_type_text",
    "identifier_type_user_selected",
    "identifier_system",
    "identifier_value",
    "identifier_period_start",
    "identifier_period_end",
)


def _reference_kwargs(prefix: str, payload) -> dict:
    """Build `{prefix}_identifier_*` ORM constructor kwargs from a payload's
    matching fields — the logical-reference fallback used alongside every
    flattened `{prefix}_type`/`{prefix}_id`/`{prefix}_display` Reference field
    (managingOrganization, contact.organization, generalPractitioner,
    link.other, identifier.assigner) for when the target isn't a resource in
    this system."""
    return {
        f"{prefix}_{suffix}": getattr(payload, f"{prefix}_{suffix}")
        for suffix in _IDENTIFIER_FALLBACK_SUFFIXES
    }


def _org_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM constructor
    kwargs from a FHIR reference string (e.g. 'Organization/100') — used for
    the two Reference(Organization) fields still expressed as a single string
    field on the payload (managingOrganization, contact.organization,
    identifier.assigner) rather than separate type+id fields."""
    ref_type, ref_id = _parse_org_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


async def _validate_reference(session, org_id, ref_type, ref_id, field_name: str) -> None:
    """Confirms a resolved `type`+`id` reference actually exists, scoped to
    the acting patient's own org_id — the identifier fallback is the intended
    path for anything cross-org/external, so a resolved reference can safely
    assume same-tenant. No-op when either half is absent (nothing to check)."""
    if ref_type and ref_id:
        await ensure_resource_exists(
            session, ref_type, ref_id, org_id=org_id, field_name=field_name
        )


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

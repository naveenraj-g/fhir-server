from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import OrganizationReferenceType
from app.models.flag import (
    FlagAuthorReferenceType,
    FlagCategory,
    FlagCategoryCoding,
    FlagCodeCoding,
    FlagEncounterReferenceType,
    FlagIdentifier,
    FlagIdentifierTypeCoding,
    FlagModel,
    FlagSubjectReferenceType,
)

_SORTABLE_FIELDS = {
    "flag_id": FlagModel.flag_id,
    "status": FlagModel.status,
    "period_start": FlagModel.period_start,
    "period_end": FlagModel.period_end,
    "created_at": FlagModel.created_at,
    "updated_at": FlagModel.updated_at,
}


def _parse_subject_ref(ref: str) -> tuple:
    return parse_reference(ref, FlagSubjectReferenceType)


def _parse_encounter_ref(ref: str) -> tuple:
    return parse_reference(ref, FlagEncounterReferenceType)


def _parse_author_ref(ref: str) -> tuple:
    return parse_reference(ref, FlagAuthorReferenceType)


def _parse_assigner_ref(ref: str) -> tuple:
    return parse_reference(ref, OrganizationReferenceType)


async def _validate_ref(
    session, org_id: str, ref_type, ref_id: int | None, field_name: str
) -> None:
    if not ref_type or ref_id is None:
        return
    type_str = ref_type.value if hasattr(ref_type, "value") else str(ref_type)
    if type_str in RESOURCE_REGISTRY:
        await ensure_resource_exists(
            session, type_str, ref_id, org_id=org_id, field_name=field_name
        )


def _with_relationships(stmt):
    """Eager-load all Flag sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(FlagModel.identifiers).selectinload(
            FlagIdentifier.type_codings
        ),
        selectinload(FlagModel.categories).selectinload(
            FlagCategory.codings
        ),
        selectinload(FlagModel.code_codings),
    )

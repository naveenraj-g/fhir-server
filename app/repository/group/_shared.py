from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import OrganizationReferenceType
from app.models.group import (
    GroupCharacteristic,
    GroupCodeCoding,
    GroupIdentifier,
    GroupIdentifierTypeCoding,
    GroupManagingEntityReferenceType,
    GroupMember,
    GroupMemberEntityReferenceType,
    GroupModel,
)

_SORTABLE_FIELDS = {
    "group_id": GroupModel.group_id,
    "type": GroupModel.type,
    "actual": GroupModel.actual,
    "name": GroupModel.name,
    "created_at": GroupModel.created_at,
    "updated_at": GroupModel.updated_at,
}


def _parse_managing_entity_ref(ref: str) -> tuple:
    return parse_reference(ref, GroupManagingEntityReferenceType)


def _parse_member_entity_ref(ref: str) -> tuple:
    return parse_reference(ref, GroupMemberEntityReferenceType)


def _parse_assigner_ref(ref: str) -> tuple:
    return parse_reference(ref, OrganizationReferenceType)


def _parse_generic_ref(ref: str) -> tuple[str | None, int | None]:
    parts = ref.strip().split("/")
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0], int(parts[1])
    return None, None


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
    """Eager-load all Group sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(GroupModel.identifiers).selectinload(
            GroupIdentifier.type_codings
        ),
        selectinload(GroupModel.code_codings),
        selectinload(GroupModel.characteristics).selectinload(
            GroupCharacteristic.code_codings
        ),
        selectinload(GroupModel.characteristics).selectinload(
            GroupCharacteristic.value_codeable_concept_codings
        ),
        selectinload(GroupModel.members),
    )

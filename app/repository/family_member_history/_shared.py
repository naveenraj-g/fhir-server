from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import IdentifierUse as IdentifierUseModel, OrganizationReferenceType
from app.models.family_member_history import (
    FamilyMemberHistoryCondition,
    FamilyMemberHistoryConditionNote,
    FamilyMemberHistoryIdentifier,
    FamilyMemberHistoryModel,
    FamilyMemberHistoryNote,
    FamilyMemberHistoryNoteAuthorReferenceType,
    FamilyMemberHistoryPatientReferenceType,
    FamilyMemberHistoryReasonCode,
    FamilyMemberHistoryReasonReference,
    FamilyMemberHistoryReasonReferenceType,
)

_IDENTIFIER_FALLBACK_SUFFIXES = (
    "identifier_use",
    "identifier_type_system",
    "identifier_type_version",
    "identifier_type_code",
    "identifier_type_display",
    "identifier_type_user_selected",
    "identifier_type_text",
    "identifier_system",
    "identifier_value",
    "identifier_period_start",
    "identifier_period_end",
)

_SORTABLE_FIELDS = {
    "family_member_history_id": FamilyMemberHistoryModel.family_member_history_id,
    "status": FamilyMemberHistoryModel.status,
    "date": FamilyMemberHistoryModel.date,
    "name": FamilyMemberHistoryModel.name,
    "created_at": FamilyMemberHistoryModel.created_at,
    "updated_at": FamilyMemberHistoryModel.updated_at,
}


def _reference_kwargs(prefix: str, payload) -> dict:
    """Build {prefix}_identifier_* ORM constructor kwargs from payload."""
    if payload is None:
        return {}
    res = {}
    for suffix in _IDENTIFIER_FALLBACK_SUFFIXES:
        val = getattr(payload, f"{prefix}_{suffix}", None)
        if suffix == "identifier_use" and val is not None:
            res[f"{prefix}_{suffix}"] = (
                IdentifierUseModel[val.name] if hasattr(val, "name") else val
            )
        else:
            res[f"{prefix}_{suffix}"] = val
    return res


def _parse_patient_ref(ref: str) -> tuple:
    return parse_reference(ref, FamilyMemberHistoryPatientReferenceType)


def _parse_reason_ref(ref: str) -> tuple:
    return parse_reference(ref, FamilyMemberHistoryReasonReferenceType)


def _parse_author_ref(ref: str) -> tuple:
    return parse_reference(ref, FamilyMemberHistoryNoteAuthorReferenceType)


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
    """Eager-load all FamilyMemberHistory sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(FamilyMemberHistoryModel.identifiers).selectinload(
            FamilyMemberHistoryIdentifier.type_codings
        ),
        selectinload(FamilyMemberHistoryModel.data_absent_reason_codings),
        selectinload(FamilyMemberHistoryModel.relationship_codings),
        selectinload(FamilyMemberHistoryModel.sex_codings),
        selectinload(FamilyMemberHistoryModel.reason_codes).selectinload(
            FamilyMemberHistoryReasonCode.codings
        ),
        selectinload(FamilyMemberHistoryModel.reason_references),
        selectinload(FamilyMemberHistoryModel.notes),
        selectinload(FamilyMemberHistoryModel.conditions).selectinload(
            FamilyMemberHistoryCondition.code_codings
        ),
        selectinload(FamilyMemberHistoryModel.conditions).selectinload(
            FamilyMemberHistoryCondition.outcome_codings
        ),
        selectinload(FamilyMemberHistoryModel.conditions).selectinload(
            FamilyMemberHistoryCondition.notes
        ),
    )

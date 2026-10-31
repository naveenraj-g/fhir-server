from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.care_team import (
    CareTeamAssignerReferenceType,
    CareTeamCategory,
    CareTeamCategoryCoding,
    CareTeamEncounterReferenceType,
    CareTeamIdentifier,
    CareTeamIdentifierTypeCoding,
    CareTeamManagingOrganization,
    CareTeamManagingOrganizationReferenceType,
    CareTeamModel,
    CareTeamNote,
    CareTeamNoteAuthorReferenceType,
    CareTeamParticipant,
    CareTeamParticipantMemberReferenceType,
    CareTeamParticipantOnBehalfOfReferenceType,
    CareTeamParticipantRole,
    CareTeamParticipantRoleCoding,
    CareTeamReasonCode,
    CareTeamReasonCodeCoding,
    CareTeamReasonReference,
    CareTeamReasonReferenceType,
    CareTeamSubjectReferenceType,
    CareTeamTelecom,
)
from app.models.enums import OrganizationReferenceType

_SORTABLE_FIELDS = {
    "care_team_id": CareTeamModel.care_team_id,
    "status": CareTeamModel.status,
    "name": CareTeamModel.name,
    "created_at": CareTeamModel.created_at,
    "updated_at": CareTeamModel.updated_at,
}


def _parse_subject_ref(ref: str) -> tuple:
    return parse_reference(ref, CareTeamSubjectReferenceType)


def _parse_encounter_ref(ref: str) -> tuple:
    return parse_reference(ref, CareTeamEncounterReferenceType)


def _parse_member_ref(ref: str) -> tuple:
    return parse_reference(ref, CareTeamParticipantMemberReferenceType)


def _parse_on_behalf_of_ref(ref: str) -> tuple:
    return parse_reference(ref, CareTeamParticipantOnBehalfOfReferenceType)


def _parse_reason_ref(ref: str) -> tuple:
    return parse_reference(ref, CareTeamReasonReferenceType)


def _parse_managing_org_ref(ref: str) -> tuple:
    return parse_reference(ref, CareTeamManagingOrganizationReferenceType)


def _parse_assigner_ref(ref: str) -> tuple:
    return parse_reference(ref, OrganizationReferenceType)


def _parse_note_author_ref(ref: str) -> tuple:
    return parse_reference(ref, CareTeamNoteAuthorReferenceType)


async def _validate_ref(
    session,
    org_id: str,
    res_type_enum,
    res_id: int | None,
    field_name: str,
) -> None:
    if not res_type_enum or not res_id:
        return
    res_type_str = (
        res_type_enum.value
        if hasattr(res_type_enum, "value")
        else str(res_type_enum)
    )
    if res_type_str not in RESOURCE_REGISTRY:
        return
    await ensure_resource_exists(
        session, res_type_str, res_id, org_id=org_id, field_name=field_name
    )


def _with_relationships(stmt):
    return stmt.options(
        selectinload(CareTeamModel.identifiers).selectinload(CareTeamIdentifier.type_codings),
        selectinload(CareTeamModel.categories).selectinload(CareTeamCategory.codings),
        selectinload(CareTeamModel.participants).selectinload(CareTeamParticipant.roles).selectinload(CareTeamParticipantRole.codings),
        selectinload(CareTeamModel.reason_codes).selectinload(CareTeamReasonCode.codings),
        selectinload(CareTeamModel.reason_references),
        selectinload(CareTeamModel.managing_organizations),
        selectinload(CareTeamModel.telecoms),
        selectinload(CareTeamModel.notes),
    )

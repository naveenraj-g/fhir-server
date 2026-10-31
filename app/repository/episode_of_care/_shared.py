from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import OrganizationReferenceType
from app.models.episode_of_care import (
    EpisodeOfCareAccount,
    EpisodeOfCareAccountReferenceType,
    EpisodeOfCareAssignerReferenceType,
    EpisodeOfCareCareManagerReferenceType,
    EpisodeOfCareDiagnosis,
    EpisodeOfCareDiagnosisConditionReferenceType,
    EpisodeOfCareDiagnosisRoleCoding,
    EpisodeOfCareIdentifier,
    EpisodeOfCareIdentifierTypeCoding,
    EpisodeOfCareManagingOrganizationReferenceType,
    EpisodeOfCareModel,
    EpisodeOfCarePatientReferenceType,
    EpisodeOfCareReferralRequest,
    EpisodeOfCareReferralRequestReferenceType,
    EpisodeOfCareStatusHistory,
    EpisodeOfCareTeam,
    EpisodeOfCareTeamReferenceType,
    EpisodeOfCareType,
    EpisodeOfCareTypeCoding,
)

_SORTABLE_FIELDS = {
    "episode_of_care_id": EpisodeOfCareModel.episode_of_care_id,
    "status": EpisodeOfCareModel.status,
    "created_at": EpisodeOfCareModel.created_at,
    "updated_at": EpisodeOfCareModel.updated_at,
}


def _parse_patient_ref(ref: str) -> tuple:
    return parse_reference(ref, EpisodeOfCarePatientReferenceType)


def _parse_managing_org_ref(ref: str) -> tuple:
    return parse_reference(ref, EpisodeOfCareManagingOrganizationReferenceType)


def _parse_care_manager_ref(ref: str) -> tuple:
    return parse_reference(ref, EpisodeOfCareCareManagerReferenceType)


def _parse_referral_request_ref(ref: str) -> tuple:
    return parse_reference(ref, EpisodeOfCareReferralRequestReferenceType)


def _parse_team_ref(ref: str) -> tuple:
    return parse_reference(ref, EpisodeOfCareTeamReferenceType)


def _parse_account_ref(ref: str) -> tuple:
    return parse_reference(ref, EpisodeOfCareAccountReferenceType)


def _parse_condition_ref(ref: str) -> tuple:
    return parse_reference(ref, EpisodeOfCareDiagnosisConditionReferenceType)


def _parse_assigner_ref(ref: str) -> tuple:
    return parse_reference(ref, OrganizationReferenceType)


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
        selectinload(EpisodeOfCareModel.identifiers).selectinload(
            EpisodeOfCareIdentifier.type_codings
        ),
        selectinload(EpisodeOfCareModel.status_history),
        selectinload(EpisodeOfCareModel.types).selectinload(EpisodeOfCareType.codings),
        selectinload(EpisodeOfCareModel.diagnoses).selectinload(
            EpisodeOfCareDiagnosis.role_codings
        ),
        selectinload(EpisodeOfCareModel.referral_requests),
        selectinload(EpisodeOfCareModel.teams),
        selectinload(EpisodeOfCareModel.accounts),
    )

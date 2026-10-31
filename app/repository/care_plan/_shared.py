from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.care_plan import (
    CarePlanActivity,
    CarePlanActivityDetailGoal,
    CarePlanActivityDetailPerformer,
    CarePlanActivityDetailPerformerReferenceType,
    CarePlanActivityDetailProductCoding,
    CarePlanActivityDetailReasonCode,
    CarePlanActivityDetailReasonReference,
    CarePlanActivityDetailReasonReferenceType,
    CarePlanActivityDetailStatusReasonCoding,
    CarePlanActivityOutcomeCC,
    CarePlanActivityOutcomeReference,
    CarePlanActivityProgress,
    CarePlanActivityReferenceType,
    CarePlanAddresses,
    CarePlanAddressesReferenceType,
    CarePlanAuthorReferenceType,
    CarePlanBasedOn,
    CarePlanBasedOnReferenceType,
    CarePlanCareTeam,
    CarePlanCareTeamReferenceType,
    CarePlanCategory,
    CarePlanCategoryCoding,
    CarePlanContributor,
    CarePlanContributorReferenceType,
    CarePlanEncounterReferenceType,
    CarePlanGoal,
    CarePlanGoalReferenceType,
    CarePlanIdentifier,
    CarePlanIdentifierTypeCoding,
    CarePlanLocationReferenceType,
    CarePlanModel,
    CarePlanNote,
    CarePlanPartOf,
    CarePlanPartOfReferenceType,
    CarePlanProductReferenceType,
    CarePlanReplaces,
    CarePlanReplacesReferenceType,
    CarePlanSubjectReferenceType,
)
from app.models.enums import OrganizationReferenceType

_SORTABLE_FIELDS = {
    "care_plan_id": CarePlanModel.care_plan_id,
    "status": CarePlanModel.status,
    "intent": CarePlanModel.intent,
    "title": CarePlanModel.title,
    "created": CarePlanModel.created,
    "created_at": CarePlanModel.created_at,
    "updated_at": CarePlanModel.updated_at,
}


def _parse_subject_ref(ref: str) -> tuple:
    return parse_reference(ref, CarePlanSubjectReferenceType)


def _parse_encounter_ref(ref: str) -> tuple:
    return parse_reference(ref, CarePlanEncounterReferenceType)


def _parse_author_ref(ref: str) -> tuple:
    return parse_reference(ref, CarePlanAuthorReferenceType)


def _parse_based_on_ref(ref: str) -> tuple:
    return parse_reference(ref, CarePlanBasedOnReferenceType)


def _parse_replaces_ref(ref: str) -> tuple:
    return parse_reference(ref, CarePlanReplacesReferenceType)


def _parse_part_of_ref(ref: str) -> tuple:
    return parse_reference(ref, CarePlanPartOfReferenceType)


def _parse_contributor_ref(ref: str) -> tuple:
    return parse_reference(ref, CarePlanContributorReferenceType)


def _parse_care_team_ref(ref: str) -> tuple:
    return parse_reference(ref, CarePlanCareTeamReferenceType)


def _parse_addresses_ref(ref: str) -> tuple:
    return parse_reference(ref, CarePlanAddressesReferenceType)


def _parse_goal_ref(ref: str) -> tuple:
    return parse_reference(ref, CarePlanGoalReferenceType)


def _parse_activity_ref(ref: str) -> tuple:
    return parse_reference(ref, CarePlanActivityReferenceType)


def _parse_activity_detail_performer_ref(ref: str) -> tuple:
    return parse_reference(ref, CarePlanActivityDetailPerformerReferenceType)


def _parse_activity_detail_reason_ref(ref: str) -> tuple:
    return parse_reference(ref, CarePlanActivityDetailReasonReferenceType)


def _parse_activity_detail_location_ref(ref: str) -> tuple:
    return parse_reference(ref, CarePlanLocationReferenceType)


def _parse_activity_detail_product_ref(ref: str) -> tuple:
    return parse_reference(ref, CarePlanProductReferenceType)


def _parse_assigner_ref(ref: str) -> tuple:
    return parse_reference(ref, OrganizationReferenceType)


def _parse_open_ref(ref: str) -> tuple:
    if not ref:
        return None, None, None, None
    parts = ref.split("/")
    if len(parts) == 2 and parts[1].isdigit():
        return ref, parts[0], int(parts[1]), None
    return ref, None, None, None


async def _validate_ref(session, org_id: str, ref_type, ref_id: int | None, field_name: str) -> None:
    if not ref_type or ref_id is None:
        return
    type_str = ref_type.value if hasattr(ref_type, "value") else str(ref_type)
    if type_str in RESOURCE_REGISTRY:
        await ensure_resource_exists(
            session, type_str, ref_id, org_id=org_id, field_name=field_name
        )


def _with_relationships(stmt):
    """Eager-load all CarePlan sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(CarePlanModel.identifiers).selectinload(
            CarePlanIdentifier.type_codings
        ),
        selectinload(CarePlanModel.categories).selectinload(
            CarePlanCategory.codings
        ),
        selectinload(CarePlanModel.based_on),
        selectinload(CarePlanModel.replaces),
        selectinload(CarePlanModel.part_of),
        selectinload(CarePlanModel.contributors),
        selectinload(CarePlanModel.care_teams),
        selectinload(CarePlanModel.addresses),
        selectinload(CarePlanModel.goals),
        selectinload(CarePlanModel.notes),
        selectinload(CarePlanModel.activities).selectinload(
            CarePlanActivity.outcome_codeable_concepts
        ).selectinload(CarePlanActivityOutcomeCC.codings),
        selectinload(CarePlanModel.activities).selectinload(
            CarePlanActivity.outcome_references
        ),
        selectinload(CarePlanModel.activities).selectinload(
            CarePlanActivity.progress
        ),
        selectinload(CarePlanModel.activities).selectinload(
            CarePlanActivity.detail_code_codings
        ),
        selectinload(CarePlanModel.activities).selectinload(
            CarePlanActivity.detail_reason_codes
        ).selectinload(CarePlanActivityDetailReasonCode.codings),
        selectinload(CarePlanModel.activities).selectinload(
            CarePlanActivity.detail_reason_references
        ),
        selectinload(CarePlanModel.activities).selectinload(
            CarePlanActivity.detail_goals
        ),
        selectinload(CarePlanModel.activities).selectinload(
            CarePlanActivity.detail_status_reason_codings
        ),
        selectinload(CarePlanModel.activities).selectinload(
            CarePlanActivity.detail_performers
        ),
        selectinload(CarePlanModel.activities).selectinload(
            CarePlanActivity.detail_product_codings
        ),
    )

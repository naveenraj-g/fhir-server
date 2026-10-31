from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import OrganizationReferenceType
from app.models.goal import (
    GoalAddresses,
    GoalAddressesReferenceType,
    GoalCategory,
    GoalExpressedByReferenceType,
    GoalIdentifier,
    GoalModel,
    GoalNote,
    GoalOutcomeCode,
    GoalOutcomeReference,
    GoalOutcomeReferenceType,
    GoalSubjectReferenceType,
    GoalTarget,
)

_SORTABLE_FIELDS = {
    "goal_id": GoalModel.goal_id,
    "lifecycle_status": GoalModel.lifecycle_status,
    "status_date": GoalModel.status_date,
    "start_date": GoalModel.start_date,
    "created_at": GoalModel.created_at,
    "updated_at": GoalModel.updated_at,
}


def _parse_subject_ref(ref: str) -> tuple:
    return parse_reference(ref, GoalSubjectReferenceType)


def _parse_expressed_by_ref(ref: str) -> tuple:
    return parse_reference(ref, GoalExpressedByReferenceType)


def _parse_assigner_ref(ref: str) -> tuple:
    return parse_reference(ref, OrganizationReferenceType)


def _parse_outcome_ref(ref: str) -> tuple:
    return parse_reference(ref, GoalOutcomeReferenceType)


def _parse_generic_ref(ref: str) -> tuple:
    """Parse any Type/ID reference string into (type_str, id_int)."""
    if "/" in ref:
        parts = ref.split("/", 1)
        try:
            return parts[0], int(parts[1])
        except ValueError:
            return parts[0], None
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
    """Eager-load all Goal sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(GoalModel.identifiers).selectinload(
            GoalIdentifier.type_codings
        ),
        selectinload(GoalModel.achievement_status_codings),
        selectinload(GoalModel.priority_codings),
        selectinload(GoalModel.description_codings),
        selectinload(GoalModel.start_codings),
        selectinload(GoalModel.categories).selectinload(
            GoalCategory.codings
        ),
        selectinload(GoalModel.targets).selectinload(
            GoalTarget.measure_codings
        ),
        selectinload(GoalModel.targets).selectinload(
            GoalTarget.detail_codings
        ),
        selectinload(GoalModel.addresses_list),
        selectinload(GoalModel.notes),
        selectinload(GoalModel.outcome_codes).selectinload(
            GoalOutcomeCode.codings
        ),
        selectinload(GoalModel.outcome_references),
    )

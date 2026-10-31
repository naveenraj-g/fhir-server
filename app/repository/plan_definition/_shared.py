from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import OrganizationReferenceType
from app.models.plan_definition import (
    PlanDefinitionAction,
    PlanDefinitionContact,
    PlanDefinitionGoal,
    PlanDefinitionIdentifier,
    PlanDefinitionJurisdiction,
    PlanDefinitionModel,
    PlanDefinitionSubjectReferenceType,
    PlanDefinitionTopic,
    PlanDefinitionUseContext,
    PlanDefinitionUseContextValueReferenceType,
)

_SORTABLE_FIELDS = {
    "plan_definition_id": PlanDefinitionModel.plan_definition_id,
    "created_at": PlanDefinitionModel.created_at,
    "updated_at": PlanDefinitionModel.updated_at,
    "name": PlanDefinitionModel.name,
    "title": PlanDefinitionModel.title,
    "status": PlanDefinitionModel.status,
    "date": PlanDefinitionModel.date,
}


def _parse_subject_ref(ref: str) -> tuple:
    return parse_reference(ref, PlanDefinitionSubjectReferenceType)


def _parse_assigner_ref(ref: str) -> tuple:
    return parse_reference(ref, OrganizationReferenceType)


def _parse_use_context_value_ref(ref: str) -> tuple:
    return parse_reference(ref, PlanDefinitionUseContextValueReferenceType)


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
        res_type_enum.value if hasattr(res_type_enum, "value") else str(res_type_enum)
    )
    if res_type_str not in RESOURCE_REGISTRY:
        return
    await ensure_resource_exists(
        session, res_type_str, res_id, org_id=org_id, field_name=field_name
    )


def _with_relationships(stmt):
    return stmt.options(
        selectinload(PlanDefinitionModel.identifiers).selectinload(
            PlanDefinitionIdentifier.type_codings
        ),
        selectinload(PlanDefinitionModel.type_codings),
        selectinload(PlanDefinitionModel.subject_codings),
        selectinload(PlanDefinitionModel.contacts).selectinload(
            PlanDefinitionContact.telecoms
        ),
        selectinload(PlanDefinitionModel.use_contexts).selectinload(
            PlanDefinitionUseContext.value_codings
        ),
        selectinload(PlanDefinitionModel.jurisdictions).selectinload(
            PlanDefinitionJurisdiction.codings
        ),
        selectinload(PlanDefinitionModel.topics).selectinload(
            PlanDefinitionTopic.codings
        ),
        selectinload(PlanDefinitionModel.related_artifacts),
        selectinload(PlanDefinitionModel.goals).selectinload(
            PlanDefinitionGoal.category_codings
        ),
        selectinload(PlanDefinitionModel.goals).selectinload(
            PlanDefinitionGoal.description_codings
        ),
        selectinload(PlanDefinitionModel.goals).selectinload(
            PlanDefinitionGoal.priority_codings
        ),
        selectinload(PlanDefinitionModel.goals).selectinload(
            PlanDefinitionGoal.start_codings
        ),
        selectinload(PlanDefinitionModel.actions).selectinload(
            PlanDefinitionAction.type_codings
        ),
    )

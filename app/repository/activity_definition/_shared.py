from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.activity_definition import (
    ActivityDefinitionAssignerReferenceType,
    ActivityDefinitionBodySite,
    ActivityDefinitionContact,
    ActivityDefinitionDosage,
    ActivityDefinitionIdentifier,
    ActivityDefinitionJurisdiction,
    ActivityDefinitionLocationReferenceType,
    ActivityDefinitionModel,
    ActivityDefinitionObservationRequirementReferenceType,
    ActivityDefinitionObservationResultRequirementReferenceType,
    ActivityDefinitionParticipant,
    ActivityDefinitionProductReferenceType,
    ActivityDefinitionSpecimenRequirementReferenceType,
    ActivityDefinitionSubjectReferenceType,
    ActivityDefinitionTopic,
    ActivityDefinitionUseContext,
    ActivityDefinitionUseContextValueReferenceType,
)

_SORTABLE_FIELDS = {
    "activity_definition_id": ActivityDefinitionModel.activity_definition_id,
    "created_at": ActivityDefinitionModel.created_at,
    "updated_at": ActivityDefinitionModel.updated_at,
    "name": ActivityDefinitionModel.name,
    "title": ActivityDefinitionModel.title,
    "status": ActivityDefinitionModel.status,
    "date": ActivityDefinitionModel.date,
}


def _parse_location_ref(ref: str) -> tuple:
    return parse_reference(ref, ActivityDefinitionLocationReferenceType)


def _parse_product_ref(ref: str) -> tuple:
    return parse_reference(ref, ActivityDefinitionProductReferenceType)


def _parse_subject_ref(ref: str) -> tuple:
    return parse_reference(ref, ActivityDefinitionSubjectReferenceType)


def _parse_assigner_ref(ref: str) -> tuple:
    return parse_reference(ref, ActivityDefinitionAssignerReferenceType)


def _parse_specimen_requirement_ref(ref: str) -> tuple:
    return parse_reference(ref, ActivityDefinitionSpecimenRequirementReferenceType)


def _parse_observation_requirement_ref(ref: str) -> tuple:
    return parse_reference(ref, ActivityDefinitionObservationRequirementReferenceType)


def _parse_observation_result_requirement_ref(ref: str) -> tuple:
    return parse_reference(
        ref, ActivityDefinitionObservationResultRequirementReferenceType
    )


def _parse_use_context_value_ref(ref: str) -> tuple:
    return parse_reference(ref, ActivityDefinitionUseContextValueReferenceType)


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
        selectinload(ActivityDefinitionModel.identifiers).selectinload(
            ActivityDefinitionIdentifier.type_codings
        ),
        selectinload(ActivityDefinitionModel.contacts).selectinload(
            ActivityDefinitionContact.telecoms
        ),
        selectinload(ActivityDefinitionModel.use_contexts).selectinload(
            ActivityDefinitionUseContext.value_codings
        ),
        selectinload(ActivityDefinitionModel.jurisdictions).selectinload(
            ActivityDefinitionJurisdiction.codings
        ),
        selectinload(ActivityDefinitionModel.topics).selectinload(
            ActivityDefinitionTopic.codings
        ),
        selectinload(ActivityDefinitionModel.body_sites).selectinload(
            ActivityDefinitionBodySite.codings
        ),
        selectinload(ActivityDefinitionModel.code_codings),
        selectinload(ActivityDefinitionModel.subject_codings),
        selectinload(ActivityDefinitionModel.product_codings),
        selectinload(ActivityDefinitionModel.related_artifacts),
        selectinload(ActivityDefinitionModel.participants).selectinload(
            ActivityDefinitionParticipant.role_codings
        ),
        selectinload(ActivityDefinitionModel.dosages).selectinload(
            ActivityDefinitionDosage.site_codings
        ),
        selectinload(ActivityDefinitionModel.dosages).selectinload(
            ActivityDefinitionDosage.route_codings
        ),
        selectinload(ActivityDefinitionModel.dosages).selectinload(
            ActivityDefinitionDosage.method_codings
        ),
        selectinload(ActivityDefinitionModel.dosages).selectinload(
            ActivityDefinitionDosage.as_needed_codings
        ),
        selectinload(ActivityDefinitionModel.dynamic_values),
        selectinload(ActivityDefinitionModel.specimen_requirements),
        selectinload(ActivityDefinitionModel.observation_requirements),
        selectinload(ActivityDefinitionModel.observation_result_requirements),
    )

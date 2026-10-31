from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import OrganizationReferenceType
from app.models.observation_definition import (
    ObservationDefinitionCategory,
    ObservationDefinitionCategoryCoding,
    ObservationDefinitionCodeCoding,
    ObservationDefinitionIdentifier,
    ObservationDefinitionIdentifierTypeCoding,
    ObservationDefinitionMethodCoding,
    ObservationDefinitionModel,
    ObservationDefinitionQualifiedInterval,
    ObservationDefinitionQualifiedIntervalAppliesTo,
    ObservationDefinitionQualifiedIntervalAppliesToCoding,
    ObservationDefinitionQualifiedIntervalContextCoding,
    ObservationDefinitionQuantitativeDetailsCustomaryUnitCoding,
    ObservationDefinitionQuantitativeDetailsUnitCoding,
    ObservationDefinitionValueSetReferenceType,
)

_SORTABLE_FIELDS = {
    "observation_definition_id": ObservationDefinitionModel.observation_definition_id,
    "created_at": ObservationDefinitionModel.created_at,
    "updated_at": ObservationDefinitionModel.updated_at,
    "preferred_report_name": ObservationDefinitionModel.preferred_report_name,
}


def _parse_value_set_ref(ref: str) -> tuple:
    return parse_reference(ref, ObservationDefinitionValueSetReferenceType)


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
        selectinload(ObservationDefinitionModel.identifiers).selectinload(
            ObservationDefinitionIdentifier.type_codings
        ),
        selectinload(ObservationDefinitionModel.categories).selectinload(
            ObservationDefinitionCategory.codings
        ),
        selectinload(ObservationDefinitionModel.code_codings),
        selectinload(ObservationDefinitionModel.method_codings),
        selectinload(
            ObservationDefinitionModel.quantitative_details_customary_unit_codings
        ),
        selectinload(
            ObservationDefinitionModel.quantitative_details_unit_codings
        ),
        selectinload(ObservationDefinitionModel.qualified_intervals).selectinload(
            ObservationDefinitionQualifiedInterval.context_codings
        ),
        selectinload(ObservationDefinitionModel.qualified_intervals)
        .selectinload(ObservationDefinitionQualifiedInterval.applies_tos)
        .selectinload(ObservationDefinitionQualifiedIntervalAppliesTo.codings),
    )

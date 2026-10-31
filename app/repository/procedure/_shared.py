from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import (
    EncounterReferenceType,
    LocationReferenceType,
    OrganizationReferenceType,
)
from app.models.procedure import (
    ProcedureAsserterReferenceType,
    ProcedureAuthorReferenceType,
    ProcedureBasedOn,
    ProcedureBasedOnReferenceType,
    ProcedureBodySite,
    ProcedureCategoryCoding,
    ProcedureCodeCoding,
    ProcedureComplication,
    ProcedureComplicationDetail,
    ProcedureComplicationDetailReferenceType,
    ProcedureFocalDevice,
    ProcedureFocalDeviceManipulatedReferenceType,
    ProcedureFollowUp,
    ProcedureIdentifier,
    ProcedureIdentifierTypeCoding,
    ProcedureModel,
    ProcedureNote,
    ProcedureOutcomeCoding,
    ProcedurePartOf,
    ProcedurePartOfReferenceType,
    ProcedurePerformer,
    ProcedurePerformerActorReferenceType,
    ProcedureReasonCode,
    ProcedureReasonReference,
    ProcedureReasonReferenceReferenceType,
    ProcedureRecorderReferenceType,
    ProcedureReport,
    ProcedureReportReferenceType,
    ProcedureStatusReasonCoding,
    ProcedureSubjectReferenceType,
    ProcedureUsedCode,
    ProcedureUsedReference,
    ProcedureUsedReferenceReferenceType,
)

_SORTABLE_FIELDS = {
    "procedure_id": ProcedureModel.procedure_id,
    "status": ProcedureModel.status,
    "performed_date_time": ProcedureModel.performed_date_time,
    "performed_period_start": ProcedureModel.performed_period_start,
    "created_at": ProcedureModel.created_at,
    "updated_at": ProcedureModel.updated_at,
}


def _parse_subject_ref(ref: str) -> tuple:
    return parse_reference(ref, ProcedureSubjectReferenceType)


def _parse_encounter_ref(ref: str) -> tuple:
    return parse_reference(ref, EncounterReferenceType)


def _parse_recorder_ref(ref: str) -> tuple:
    return parse_reference(ref, ProcedureRecorderReferenceType)


def _parse_asserter_ref(ref: str) -> tuple:
    return parse_reference(ref, ProcedureAsserterReferenceType)


def _parse_location_ref(ref: str) -> tuple:
    return parse_reference(ref, LocationReferenceType)


def _parse_based_on_ref(ref: str) -> tuple:
    return parse_reference(ref, ProcedureBasedOnReferenceType)


def _parse_part_of_ref(ref: str) -> tuple:
    return parse_reference(ref, ProcedurePartOfReferenceType)


def _parse_reason_reference_ref(ref: str) -> tuple:
    return parse_reference(ref, ProcedureReasonReferenceReferenceType)


def _parse_report_ref(ref: str) -> tuple:
    return parse_reference(ref, ProcedureReportReferenceType)


def _parse_complication_detail_ref(ref: str) -> tuple:
    return parse_reference(ref, ProcedureComplicationDetailReferenceType)


def _parse_used_reference_ref(ref: str) -> tuple:
    return parse_reference(ref, ProcedureUsedReferenceReferenceType)


def _parse_performer_actor_ref(ref: str) -> tuple:
    return parse_reference(ref, ProcedurePerformerActorReferenceType)


def _parse_performer_on_behalf_of_ref(ref: str) -> tuple:
    return parse_reference(ref, OrganizationReferenceType)


def _parse_focal_device_manipulated_ref(ref: str) -> tuple:
    return parse_reference(ref, ProcedureFocalDeviceManipulatedReferenceType)


def _parse_author_ref(ref: str) -> tuple:
    return parse_reference(ref, ProcedureAuthorReferenceType)


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
    """Eager-load all Procedure sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(ProcedureModel.identifiers).selectinload(
            ProcedureIdentifier.type_codings
        ),
        selectinload(ProcedureModel.based_on),
        selectinload(ProcedureModel.part_of),
        selectinload(ProcedureModel.status_reason_codings),
        selectinload(ProcedureModel.category_codings),
        selectinload(ProcedureModel.code_codings),
        selectinload(ProcedureModel.performers).selectinload(
            ProcedurePerformer.function_codings
        ),
        selectinload(ProcedureModel.reason_codes).selectinload(
            ProcedureReasonCode.codings
        ),
        selectinload(ProcedureModel.reason_references),
        selectinload(ProcedureModel.body_sites).selectinload(
            ProcedureBodySite.codings
        ),
        selectinload(ProcedureModel.outcome_codings),
        selectinload(ProcedureModel.reports),
        selectinload(ProcedureModel.complications).selectinload(
            ProcedureComplication.codings
        ),
        selectinload(ProcedureModel.complication_details),
        selectinload(ProcedureModel.follow_ups).selectinload(
            ProcedureFollowUp.codings
        ),
        selectinload(ProcedureModel.notes),
        selectinload(ProcedureModel.focal_devices).selectinload(
            ProcedureFocalDevice.action_codings
        ),
        selectinload(ProcedureModel.used_references),
        selectinload(ProcedureModel.used_codes).selectinload(
            ProcedureUsedCode.codings
        ),
    )

from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import OrganizationReferenceType
from app.models.task import (
    TaskBasedOn,
    TaskBusinessStatusCoding,
    TaskCodeCoding,
    TaskEncounterReferenceType,
    TaskIdentifier,
    TaskIdentifierTypeCoding,
    TaskInput,
    TaskInputTypeCoding,
    TaskInsurance,
    TaskInsuranceReferenceType,
    TaskLocationReferenceType,
    TaskModel,
    TaskNote,
    TaskOutput,
    TaskOutputTypeCoding,
    TaskOwnerReferenceType,
    TaskPartOf,
    TaskPartOfReferenceType,
    TaskPerformerType,
    TaskPerformerTypeCoding,
    TaskReasonCodeCoding,
    TaskRelevantHistory,
    TaskRelevantHistoryReferenceType,
    TaskRequesterReferenceType,
    TaskRestrictionRecipient,
    TaskRestrictionRecipientReferenceType,
    TaskStatusReasonCoding,
)

_SORTABLE_FIELDS = {
    "task_id": TaskModel.task_id,
    "status": TaskModel.status,
    "intent": TaskModel.intent,
    "priority": TaskModel.priority,
    "authored_on": TaskModel.authored_on,
    "last_modified": TaskModel.last_modified,
    "created_at": TaskModel.created_at,
    "updated_at": TaskModel.updated_at,
}


def _parse_requester_ref(ref: str) -> tuple:
    return parse_reference(ref, TaskRequesterReferenceType)


def _parse_owner_ref(ref: str) -> tuple:
    return parse_reference(ref, TaskOwnerReferenceType)


def _parse_location_ref(ref: str) -> tuple:
    return parse_reference(ref, TaskLocationReferenceType)


def _parse_encounter_ref(ref: str) -> tuple:
    return parse_reference(ref, TaskEncounterReferenceType)


def _parse_assigner_ref(ref: str) -> tuple:
    return parse_reference(ref, OrganizationReferenceType)


def _parse_insurance_ref(ref: str) -> tuple:
    return parse_reference(ref, TaskInsuranceReferenceType)


def _parse_relevant_history_ref(ref: str) -> tuple:
    return parse_reference(ref, TaskRelevantHistoryReferenceType)


def _parse_part_of_ref(ref: str) -> tuple:
    return parse_reference(ref, TaskPartOfReferenceType)


def _parse_recipient_ref(ref: str) -> tuple:
    return parse_reference(ref, TaskRestrictionRecipientReferenceType)


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
    """Eager-load all Task sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(TaskModel.identifiers).selectinload(
            TaskIdentifier.type_codings
        ),
        selectinload(TaskModel.based_on_list),
        selectinload(TaskModel.part_of_list),
        selectinload(TaskModel.insurance_list),
        selectinload(TaskModel.relevant_history_list),
        selectinload(TaskModel.restriction_recipients),
        selectinload(TaskModel.performer_types).selectinload(
            TaskPerformerType.codings
        ),
        selectinload(TaskModel.code_codings),
        selectinload(TaskModel.status_reason_codings),
        selectinload(TaskModel.business_status_codings),
        selectinload(TaskModel.reason_code_codings),
        selectinload(TaskModel.notes),
        selectinload(TaskModel.inputs).selectinload(
            TaskInput.type_codings
        ),
        selectinload(TaskModel.outputs).selectinload(
            TaskOutput.type_codings
        ),
    )

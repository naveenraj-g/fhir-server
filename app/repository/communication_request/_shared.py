from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.communication_request import (
    CommunicationRequestAbout,
    CommunicationRequestBasedOn,
    CommunicationRequestCategory,
    CommunicationRequestEncounterReferenceType,
    CommunicationRequestIdentifier,
    CommunicationRequestMedium,
    CommunicationRequestModel,
    CommunicationRequestNote,
    CommunicationRequestPayload,
    CommunicationRequestReasonCode,
    CommunicationRequestReasonReference,
    CommunicationRequestReasonReferenceType,
    CommunicationRequestRecipient,
    CommunicationRequestRecipientReferenceType,
    CommunicationRequestReplaces,
    CommunicationRequestRequesterReferenceType,
    CommunicationRequestSenderReferenceType,
    CommunicationRequestSubjectReferenceType,
)
from app.models.enums import OrganizationReferenceType

_SORTABLE_FIELDS = {
    "communication_request_id": CommunicationRequestModel.communication_request_id,
    "status": CommunicationRequestModel.status,
    "priority": CommunicationRequestModel.priority,
    "authored_on": CommunicationRequestModel.authored_on,
    "occurrence_date_time": CommunicationRequestModel.occurrence_date_time,
    "created_at": CommunicationRequestModel.created_at,
    "updated_at": CommunicationRequestModel.updated_at,
}


def _parse_subject_ref(ref: str) -> tuple:
    return parse_reference(ref, CommunicationRequestSubjectReferenceType)


def _parse_encounter_ref(ref: str) -> tuple:
    return parse_reference(ref, CommunicationRequestEncounterReferenceType)


def _parse_requester_ref(ref: str) -> tuple:
    return parse_reference(ref, CommunicationRequestRequesterReferenceType)


def _parse_recipient_ref(ref: str) -> tuple:
    return parse_reference(ref, CommunicationRequestRecipientReferenceType)


def _parse_sender_ref(ref: str) -> tuple:
    return parse_reference(ref, CommunicationRequestSenderReferenceType)


def _parse_reason_ref(ref: str) -> tuple:
    return parse_reference(ref, CommunicationRequestReasonReferenceType)


def _parse_assigner_ref(ref: str) -> tuple:
    return parse_reference(ref, OrganizationReferenceType)


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
    """Eager-load all CommunicationRequest sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(CommunicationRequestModel.identifiers).selectinload(
            CommunicationRequestIdentifier.type_codings
        ),
        selectinload(CommunicationRequestModel.based_on_list),
        selectinload(CommunicationRequestModel.replaces_list),
        selectinload(CommunicationRequestModel.status_reason_codings),
        selectinload(CommunicationRequestModel.categories).selectinload(
            CommunicationRequestCategory.codings
        ),
        selectinload(CommunicationRequestModel.medium_list).selectinload(
            CommunicationRequestMedium.codings
        ),
        selectinload(CommunicationRequestModel.about_list),
        selectinload(CommunicationRequestModel.payloads),
        selectinload(CommunicationRequestModel.recipients),
        selectinload(CommunicationRequestModel.reason_codes).selectinload(
            CommunicationRequestReasonCode.codings
        ),
        selectinload(CommunicationRequestModel.reason_references),
        selectinload(CommunicationRequestModel.notes),
    )

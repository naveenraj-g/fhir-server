from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.communication import (
    CommunicationAbout,
    CommunicationBasedOn,
    CommunicationCategory,
    CommunicationEncounterReferenceType,
    CommunicationIdentifier,
    CommunicationInResponseTo,
    CommunicationInResponseToReferenceType,
    CommunicationMedium,
    CommunicationModel,
    CommunicationNote,
    CommunicationPartOf,
    CommunicationPayload,
    CommunicationReasonCode,
    CommunicationReasonReference,
    CommunicationReasonReferenceType,
    CommunicationRecipient,
    CommunicationRecipientReferenceType,
    CommunicationSenderReferenceType,
    CommunicationStatusReasonCoding,
    CommunicationSubjectReferenceType,
    CommunicationTopicCoding,
)
from app.models.enums import OrganizationReferenceType
from app.repository._reference_shared import _IDENTIFIER_FALLBACK_SUFFIXES


def _prefixed_identifier_kwargs(prefix: str, payload) -> dict:
    if payload is None:
        return {f"{prefix}_{suffix}": None for suffix in _IDENTIFIER_FALLBACK_SUFFIXES}
    return {
        f"{prefix}_{suffix}": getattr(payload, f"{prefix}_{suffix}", None)
        for suffix in _IDENTIFIER_FALLBACK_SUFFIXES
    }


def _child_reference_identifier_kwargs(ref_item) -> dict:
    if isinstance(ref_item, str) or ref_item is None:
        return {f"reference_{suffix}": None for suffix in _IDENTIFIER_FALLBACK_SUFFIXES}
    return {
        f"reference_{suffix}": getattr(ref_item, suffix, None)
        for suffix in _IDENTIFIER_FALLBACK_SUFFIXES
    }

_SORTABLE_FIELDS = {
    "communication_id": CommunicationModel.communication_id,
    "status": CommunicationModel.status,
    "priority": CommunicationModel.priority,
    "sent": CommunicationModel.sent,
    "received": CommunicationModel.received,
    "created_at": CommunicationModel.created_at,
    "updated_at": CommunicationModel.updated_at,
}


def _parse_subject_ref(ref: str) -> tuple:
    return parse_reference(ref, CommunicationSubjectReferenceType)


def _parse_encounter_ref(ref: str) -> tuple:
    return parse_reference(ref, CommunicationEncounterReferenceType)


def _parse_sender_ref(ref: str) -> tuple:
    return parse_reference(ref, CommunicationSenderReferenceType)


def _parse_recipient_ref(ref: str) -> tuple:
    return parse_reference(ref, CommunicationRecipientReferenceType)


def _parse_in_response_to_ref(ref: str) -> tuple:
    return parse_reference(ref, CommunicationInResponseToReferenceType)


def _parse_reason_ref(ref: str) -> tuple:
    return parse_reference(ref, CommunicationReasonReferenceType)


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
    """Eager-load all Communication sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(CommunicationModel.identifiers).selectinload(
            CommunicationIdentifier.type_codings
        ),
        selectinload(CommunicationModel.based_on_list),
        selectinload(CommunicationModel.part_of_list),
        selectinload(CommunicationModel.in_response_to_list),
        selectinload(CommunicationModel.status_reason_codings),
        selectinload(CommunicationModel.categories).selectinload(
            CommunicationCategory.codings
        ),
        selectinload(CommunicationModel.medium_list).selectinload(
            CommunicationMedium.codings
        ),
        selectinload(CommunicationModel.topic_codings),
        selectinload(CommunicationModel.about_list),
        selectinload(CommunicationModel.recipients),
        selectinload(CommunicationModel.reason_codes).selectinload(
            CommunicationReasonCode.codings
        ),
        selectinload(CommunicationModel.reason_references),
        selectinload(CommunicationModel.payloads),
        selectinload(CommunicationModel.notes),
    )

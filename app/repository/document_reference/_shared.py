from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.document_reference import (
    DocumentReferenceAuthenticatorReferenceType,
    DocumentReferenceAuthorReferenceType,
    DocumentReferenceCategory,
    DocumentReferenceContextEncounterReferenceType,
    DocumentReferenceContextEvent,
    DocumentReferenceDocStatus as DocumentReferenceDocStatusModel,
    DocumentReferenceIdentifier,
    DocumentReferenceModel,
    DocumentReferencePatientReferenceType,
    DocumentReferenceSecurityLabel,
    DocumentReferenceStatus as DocumentReferenceStatusModel,
    DocumentReferenceSubjectReferenceType,
    DocumentReferenceTargetReferenceType,
    DocumentRelationshipType as DocumentRelationshipTypeModel,
)
from app.models.enums import IdentifierUse as IdentifierUseModel, OrganizationReferenceType

_SORTABLE_FIELDS = {
    "document_reference_id": DocumentReferenceModel.document_reference_id,
    "status": DocumentReferenceModel.status,
    "date": DocumentReferenceModel.date,
    "created_at": DocumentReferenceModel.created_at,
    "updated_at": DocumentReferenceModel.updated_at,
}


def _parse_subject_ref(ref: str) -> tuple:
    return parse_reference(ref, DocumentReferenceSubjectReferenceType)


def _parse_author_ref(ref: str) -> tuple:
    return parse_reference(ref, DocumentReferenceAuthorReferenceType)


def _parse_authenticator_ref(ref: str) -> tuple:
    return parse_reference(ref, DocumentReferenceAuthenticatorReferenceType)


def _parse_custodian_ref(ref: str) -> tuple:
    return parse_reference(ref, OrganizationReferenceType)


def _parse_target_ref(ref: str) -> tuple:
    return parse_reference(ref, DocumentReferenceTargetReferenceType)


def _parse_context_encounter_ref(ref: str) -> tuple:
    return parse_reference(ref, DocumentReferenceContextEncounterReferenceType)


def _parse_context_patient_ref(ref: str) -> tuple:
    return parse_reference(ref, DocumentReferencePatientReferenceType)


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
    """Eager-load all DocumentReference sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(DocumentReferenceModel.master_identifier_type_codings),
        selectinload(DocumentReferenceModel.identifiers).selectinload(
            DocumentReferenceIdentifier.type_codings
        ),
        selectinload(DocumentReferenceModel.type_codings),
        selectinload(DocumentReferenceModel.categories).selectinload(
            DocumentReferenceCategory.codings
        ),
        selectinload(DocumentReferenceModel.authors),
        selectinload(DocumentReferenceModel.relates_to),
        selectinload(DocumentReferenceModel.security_labels).selectinload(
            DocumentReferenceSecurityLabel.codings
        ),
        selectinload(DocumentReferenceModel.contents),
        selectinload(DocumentReferenceModel.context_encounters),
        selectinload(DocumentReferenceModel.context_events).selectinload(
            DocumentReferenceContextEvent.codings
        ),
        selectinload(DocumentReferenceModel.context_facility_type_codings),
        selectinload(DocumentReferenceModel.context_practice_setting_codings),
        selectinload(DocumentReferenceModel.context_related),
    )

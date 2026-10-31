from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.enums import OrganizationReferenceType
from app.models.related_person import (
    RelatedPersonAddress,
    RelatedPersonCommunication,
    RelatedPersonCommunicationLanguageCoding,
    RelatedPersonIdentifier,
    RelatedPersonIdentifierTypeCoding,
    RelatedPersonModel,
    RelatedPersonName,
    RelatedPersonPatientReferenceType,
    RelatedPersonPhoto,
    RelatedPersonRelationship,
    RelatedPersonRelationshipCoding,
    RelatedPersonTelecom,
)

_SORTABLE_FIELDS = {
    "related_person_id": RelatedPersonModel.related_person_id,
    "active": RelatedPersonModel.active,
    "gender": RelatedPersonModel.gender,
    "birth_date": RelatedPersonModel.birth_date,
    "created_at": RelatedPersonModel.created_at,
    "updated_at": RelatedPersonModel.updated_at,
}


def _parse_patient_ref(ref: str) -> tuple:
    return parse_reference(ref, RelatedPersonPatientReferenceType)


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
    """Eager-load all RelatedPerson sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(RelatedPersonModel.identifiers).selectinload(
            RelatedPersonIdentifier.type_codings
        ),
        selectinload(RelatedPersonModel.relationships).selectinload(
            RelatedPersonRelationship.codings
        ),
        selectinload(RelatedPersonModel.names),
        selectinload(RelatedPersonModel.telecoms),
        selectinload(RelatedPersonModel.addresses),
        selectinload(RelatedPersonModel.photos),
        selectinload(RelatedPersonModel.communications).selectinload(
            RelatedPersonCommunication.language_codings
        ),
    )

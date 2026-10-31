from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.core.reference_resolver import RESOURCE_REGISTRY, ensure_resource_exists
from app.models.consent import (
    ConsentCategory,
    ConsentIdentifier,
    ConsentModel,
    ConsentPatientReferenceType,
    ConsentPerformerReferenceType,
    ConsentProvision,
    ConsentProvisionAction,
    ConsentProvisionActor,
    ConsentProvisionCode,
    ConsentProvisionActorReferenceType,
    ConsentSourceReferenceType,
    ConsentVerifiedWithReferenceType,
)
from app.models.enums import OrganizationReferenceType

_SORTABLE_FIELDS = {
    "consent_id": ConsentModel.consent_id,
    "status": ConsentModel.status,
    "date_time": ConsentModel.date_time,
    "created_at": ConsentModel.created_at,
    "updated_at": ConsentModel.updated_at,
}


def _parse_patient_ref(ref: str) -> tuple:
    return parse_reference(ref, ConsentPatientReferenceType)


def _parse_performer_ref(ref: str) -> tuple:
    return parse_reference(ref, ConsentPerformerReferenceType)


def _parse_organization_ref(ref: str) -> tuple:
    return parse_reference(ref, OrganizationReferenceType)


def _parse_source_ref(ref: str) -> tuple:
    return parse_reference(ref, ConsentSourceReferenceType)


def _parse_verified_with_ref(ref: str) -> tuple:
    return parse_reference(ref, ConsentVerifiedWithReferenceType)


def _parse_actor_ref(ref: str) -> tuple:
    return parse_reference(ref, ConsentProvisionActorReferenceType)


def _parse_assigner_ref(ref: str) -> tuple:
    return parse_reference(ref, OrganizationReferenceType)


def _parse_generic_ref(ref: str) -> tuple[str | None, int | None]:
    parts = ref.strip().split("/")
    if len(parts) == 2 and parts[1].isdigit():
        return parts[0], int(parts[1])
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
    """Eager-load all Consent sub-resources to avoid N+1 and async lazy-load failures."""
    return stmt.options(
        selectinload(ConsentModel.identifiers).selectinload(
            ConsentIdentifier.type_codings
        ),
        selectinload(ConsentModel.scope_codings),
        selectinload(ConsentModel.categories).selectinload(
            ConsentCategory.codings
        ),
        selectinload(ConsentModel.performers),
        selectinload(ConsentModel.organizations),
        selectinload(ConsentModel.policies),
        selectinload(ConsentModel.policy_rule_codings),
        selectinload(ConsentModel.verifications),
        selectinload(ConsentModel.provisions).selectinload(
            ConsentProvision.sub_provisions
        ),
        selectinload(ConsentModel.provisions)
        .selectinload(ConsentProvision.actors)
        .selectinload(ConsentProvisionActor.role_codings),
        selectinload(ConsentModel.provisions)
        .selectinload(ConsentProvision.actions)
        .selectinload(ConsentProvisionAction.codings),
        selectinload(ConsentModel.provisions).selectinload(
            ConsentProvision.security_labels
        ),
        selectinload(ConsentModel.provisions).selectinload(
            ConsentProvision.purposes
        ),
        selectinload(ConsentModel.provisions).selectinload(
            ConsentProvision.classes
        ),
        selectinload(ConsentModel.provisions)
        .selectinload(ConsentProvision.codes)
        .selectinload(ConsentProvisionCode.codings),
        selectinload(ConsentModel.provisions).selectinload(
            ConsentProvision.data_entries
        ),
    )

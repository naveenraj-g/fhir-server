from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.patient import (
    PatientCommunication,
    PatientContact,
    PatientContactRelationship,
    PatientIdentifier,
    PatientModel,
)
from app.models.patient.enums import (
    PatientGeneralPractitionerReferenceType,
    PatientLinkOtherType,
)
from app.repository._reference_shared import (
    _org_ref_kwargs,
    _parse_org_ref,
    _validate_reference,
)

_IDENTIFIER_FALLBACK_SUFFIXES = (
    "identifier_system",
    "identifier_value",
    "identifier_use",
    "identifier_type_text",
)


def _reference_kwargs(prefix: str, payload) -> dict:
    """Build {prefix}_identifier_* ORM constructor kwargs from payload."""
    return {
        f"{prefix}_{suffix}": getattr(payload, f"{prefix}_{suffix}", None)
        for suffix in _IDENTIFIER_FALLBACK_SUFFIXES
    }

__all__ = [
    "_IDENTIFIER_FALLBACK_SUFFIXES",
    "_SORTABLE_FIELDS",
    "_org_ref_kwargs",
    "_parse_gp_ref",
    "_parse_link_ref",
    "_parse_org_ref",
    "_reference_kwargs",
    "_validate_reference",
    "_with_relationships",
]

_SORTABLE_FIELDS = {
    "patient_id": PatientModel.patient_id,
    "birth_date": PatientModel.birth_date,
    "created_at": PatientModel.created_at,
    "updated_at": PatientModel.updated_at,
}


def _parse_gp_ref(ref: str) -> tuple:
    """Parse 'Practitioner/123' -> (PatientGeneralPractitionerReferenceType.Practitioner, 123)."""
    return parse_reference(ref, PatientGeneralPractitionerReferenceType)


def _parse_link_ref(ref: str) -> tuple:
    """Parse 'Patient/123' -> (PatientLinkOtherType.Patient, 123)."""
    return parse_reference(ref, PatientLinkOtherType)


def _with_relationships(stmt):
    """Eager-load all Patient sub-resources to avoid N+1 and async
    lazy-load failures."""
    return stmt.options(
        selectinload(PatientModel.identifiers).selectinload(
            PatientIdentifier.type_codings
        ),
        selectinload(PatientModel.names),
        selectinload(PatientModel.telecoms),
        selectinload(PatientModel.addresses),
        selectinload(PatientModel.photos),
        selectinload(PatientModel.marital_status_codings),
        selectinload(PatientModel.contacts)
        .selectinload(PatientContact.relationships)
        .selectinload(PatientContactRelationship.codings),
        selectinload(PatientModel.contacts).selectinload(PatientContact.telecoms),
        selectinload(PatientModel.communications).selectinload(
            PatientCommunication.language_codings
        ),
        selectinload(PatientModel.general_practitioners),
        selectinload(PatientModel.links),
    )

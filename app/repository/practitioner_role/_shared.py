from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.enums import PractitionerReferenceType
from app.models.practitioner_role import (
    PractitionerRoleEndpointReferenceType,
    PractitionerRoleHealthcareServiceReferenceType,
    PractitionerRoleLocationReferenceType,
    PractitionerRoleModel,
)
from app.repository._reference_shared import (
    _IDENTIFIER_FALLBACK_SUFFIXES,
    _org_ref_kwargs,
    _parse_org_ref,
    _reference_kwargs,
    _validate_reference,
)

__all__ = [
    "_IDENTIFIER_FALLBACK_SUFFIXES",
    "REFERENCE_PARSERS",
    "_org_ref_kwargs",
    "_parse_endpoint_ref",
    "_parse_healthcare_service_ref",
    "_parse_location_ref",
    "_parse_org_ref",
    "_parse_practitioner_ref",
    "_reference_kwargs",
    "_validate_reference",
    "_with_relationships",
]


def _with_relationships(stmt):
    """Eager-load the search-index child rows. Only needed when a write is
    about to replace them (patch_full) — reads never touch them, since every
    response is served straight from PractitionerRoleModel.content."""
    return stmt.options(
        *(
            selectinload(getattr(PractitionerRoleModel, rel))
            for rel in ("identifiers", "telecoms", "tokens", "references")
        )
    )


def _parse_practitioner_ref(ref: str) -> tuple:
    """Parse 'Practitioner/30001' → (PractitionerReferenceType.Practitioner, 30001)."""
    return parse_reference(ref, PractitionerReferenceType)


def _parse_location_ref(ref: str) -> tuple:
    """Parse 'Location/230001' → (PractitionerRoleLocationReferenceType.Location, 230001)."""
    return parse_reference(ref, PractitionerRoleLocationReferenceType)


def _parse_healthcare_service_ref(ref: str) -> tuple:
    """Parse 'HealthcareService/150001'."""
    return parse_reference(ref, PractitionerRoleHealthcareServiceReferenceType)


def _parse_endpoint_ref(ref: str) -> tuple:
    """Parse 'Endpoint/620001'. Endpoint is a resource on this server
    (RESOURCE_REGISTRY), so a relative Endpoint/<id> is existence-checked on
    write; an endpoint given only by identifier/display simply has no index row."""
    return parse_reference(ref, PractitionerRoleEndpointReferenceType)


# resource type of a local reference -> how to parse it into (enum, public id)
REFERENCE_PARSERS = {
    "Practitioner": _parse_practitioner_ref,
    "Organization": _parse_org_ref,
    "Location": _parse_location_ref,
    "HealthcareService": _parse_healthcare_service_ref,
    "Endpoint": _parse_endpoint_ref,
}

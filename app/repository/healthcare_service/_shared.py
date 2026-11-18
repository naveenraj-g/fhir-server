from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.healthcare_service import (
    HealthcareServiceEndpointReferenceType,
    HealthcareServiceLocationReferenceType,
    HealthcareServiceModel,
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
    "_org_ref_kwargs",
    "_parse_endpoint_ref",
    "_parse_location_ref",
    "_parse_org_ref",
    "_reference_kwargs",
    "_validate_reference",
    "_with_relationships",
]


def _with_relationships(stmt):
    """Eager-load the search-index child rows. Only needed when a write is
    about to replace them (patch_full) — reads never touch them, since every
    response is served straight from HealthcareServiceModel.content."""
    return stmt.options(
        *(
            selectinload(getattr(HealthcareServiceModel, rel))
            for rel in ("identifiers", "tokens", "references")
        )
    )


def _parse_location_ref(ref: str) -> tuple:
    """Parse 'Location/230001' → (HealthcareServiceLocationReferenceType.Location, 230001)."""
    return parse_reference(ref, HealthcareServiceLocationReferenceType)


def _parse_endpoint_ref(ref: str) -> tuple:
    """Parse 'Endpoint/1'. Endpoint is a resource on this server
    (RESOURCE_REGISTRY), so a relative Endpoint/<id> is existence-checked on
    write; an endpoint given only by identifier/display simply has no index row."""
    return parse_reference(ref, HealthcareServiceEndpointReferenceType)

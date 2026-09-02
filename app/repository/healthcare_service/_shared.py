from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.healthcare_service import HealthcareServiceModel
from app.models.healthcare_service.enums import (
    HealthcareServiceCoverageAreaReferenceType,
    HealthcareServiceEndpointReferenceType,
    HealthcareServiceLocationReferenceType,
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
    "_SORTABLE_FIELDS",
    "_coverage_area_ref_kwargs",
    "_location_ref_kwargs",
    "_org_ref_kwargs",
    "_parse_coverage_area_ref",
    "_parse_endpoint_ref",
    "_parse_location_ref",
    "_parse_org_ref",
    "_reference_kwargs",
    "_validate_reference",
    "_with_relationships",
]


# Sortable fields exposed via the `sort` list-query param (see
# app.core.pagination.resolve_sort) — mirrors Organization's _shared.py.
_SORTABLE_FIELDS = {
    "healthcare_service_id": HealthcareServiceModel.healthcare_service_id,
    "name": HealthcareServiceModel.name,
    "created_at": HealthcareServiceModel.created_at,
    "updated_at": HealthcareServiceModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load all 16 healthcare_service sub-resources to avoid N+1 and
    async lazy-load failures."""
    return stmt.options(
        selectinload(HealthcareServiceModel.identifiers),
        selectinload(HealthcareServiceModel.categories),
        selectinload(HealthcareServiceModel.types),
        selectinload(HealthcareServiceModel.specialties),
        selectinload(HealthcareServiceModel.locations),
        selectinload(HealthcareServiceModel.telecoms),
        selectinload(HealthcareServiceModel.coverage_areas),
        selectinload(HealthcareServiceModel.service_provision_codes),
        selectinload(HealthcareServiceModel.eligibilities),
        selectinload(HealthcareServiceModel.programs),
        selectinload(HealthcareServiceModel.characteristics),
        selectinload(HealthcareServiceModel.communications),
        selectinload(HealthcareServiceModel.referral_methods),
        selectinload(HealthcareServiceModel.available_times),
        selectinload(HealthcareServiceModel.not_available),
        selectinload(HealthcareServiceModel.endpoints),
    )


def _parse_location_ref(ref: str) -> tuple:
    """Parse 'Location/230001' → (HealthcareServiceLocationReferenceType.Location, 230001)."""
    return parse_reference(ref, HealthcareServiceLocationReferenceType)


def _parse_coverage_area_ref(ref: str) -> tuple:
    """Parse 'Location/230001' → (HealthcareServiceCoverageAreaReferenceType.Location, 230001)."""
    return parse_reference(ref, HealthcareServiceCoverageAreaReferenceType)


def _parse_endpoint_ref(ref: str) -> tuple:
    """Parse 'Endpoint/1' → (HealthcareServiceEndpointReferenceType.Endpoint, 1).
    Endpoint isn't a modeled resource in this system (no RESOURCE_REGISTRY
    entry, see app/core/reference_resolver.py) so — unlike location/
    coverageArea/providedBy — there's no existence check to run here; the
    identifier fallback (see HealthcareServiceEndpointInput) is often the
    only populated half."""
    return parse_reference(ref, HealthcareServiceEndpointReferenceType)


def _location_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM constructor
    kwargs from a FHIR reference string (e.g. 'Location/230001') for the
    HealthcareService.location[] Reference(Location) field."""
    ref_type, ref_id = _parse_location_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


def _coverage_area_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    """Same as `_location_ref_kwargs` for HealthcareService.coverageArea[] —
    a distinct Enum type from `.location[]` even though both target Location,
    since each flattened reference column family owns its own PG enum type."""
    ref_type, ref_id = _parse_coverage_area_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }

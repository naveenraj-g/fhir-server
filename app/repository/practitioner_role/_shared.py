from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.practitioner_role import PractitionerRoleModel
from app.models.practitioner_role.enums import (
    PractitionerRoleEndpointReferenceType,
    PractitionerRoleHealthcareServiceReferenceType,
    PractitionerRoleLocationReferenceType,
    PractitionerRolePractitionerReferenceType,
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
    "_healthcare_service_ref_kwargs",
    "_location_ref_kwargs",
    "_org_ref_kwargs",
    "_parse_endpoint_ref",
    "_parse_healthcare_service_ref",
    "_parse_location_ref",
    "_parse_org_ref",
    "_parse_practitioner_ref",
    "_practitioner_ref_kwargs",
    "_reference_kwargs",
    "_validate_reference",
    "_with_relationships",
]


# Sortable fields exposed via the `sort` list-query param (see
# app.core.pagination.resolve_sort) — mirrors HealthcareService's _shared.py.
_SORTABLE_FIELDS = {
    "practitioner_role_id": PractitionerRoleModel.practitioner_role_id,
    "created_at": PractitionerRoleModel.created_at,
    "updated_at": PractitionerRoleModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load all 9 practitioner_role sub-resources to avoid N+1 and
    async lazy-load failures."""
    return stmt.options(
        selectinload(PractitionerRoleModel.identifiers),
        selectinload(PractitionerRoleModel.codes),
        selectinload(PractitionerRoleModel.specialties),
        selectinload(PractitionerRoleModel.locations),
        selectinload(PractitionerRoleModel.healthcare_services),
        selectinload(PractitionerRoleModel.telecoms),
        selectinload(PractitionerRoleModel.available_times),
        selectinload(PractitionerRoleModel.not_available),
        selectinload(PractitionerRoleModel.endpoints),
    )


def _parse_practitioner_ref(ref: str) -> tuple:
    """Parse 'Practitioner/30001' → (PractitionerRolePractitionerReferenceType.Practitioner, 30001)."""
    return parse_reference(ref, PractitionerRolePractitionerReferenceType)


def _practitioner_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM constructor
    kwargs from a FHIR reference string (e.g. 'Practitioner/30001') for the
    PractitionerRole.practitioner Reference(Practitioner) field."""
    ref_type, ref_id = _parse_practitioner_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


def _parse_location_ref(ref: str) -> tuple:
    """Parse 'Location/230001' → (PractitionerRoleLocationReferenceType.Location, 230001)."""
    return parse_reference(ref, PractitionerRoleLocationReferenceType)


def _location_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM constructor
    kwargs from a FHIR reference string (e.g. 'Location/230001') for the
    PractitionerRole.location[] Reference(Location) field."""
    ref_type, ref_id = _parse_location_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


def _parse_healthcare_service_ref(ref: str) -> tuple:
    """Parse 'HealthcareService/150001' → (PractitionerRoleHealthcareServiceReferenceType.HealthcareService, 150001)."""
    return parse_reference(ref, PractitionerRoleHealthcareServiceReferenceType)


def _healthcare_service_ref_kwargs(
    prefix: str, ref: str | None, display: str | None
) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM constructor
    kwargs from a FHIR reference string (e.g. 'HealthcareService/150001') for
    the PractitionerRole.healthcareService[] Reference(HealthcareService) field."""
    ref_type, ref_id = _parse_healthcare_service_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


def _parse_endpoint_ref(ref: str) -> tuple:
    """Parse 'Endpoint/1' → (PractitionerRoleEndpointReferenceType.Endpoint, 1).
    Endpoint isn't a modeled resource in this system (no RESOURCE_REGISTRY
    entry, see app/core/reference_resolver.py) so — unlike practitioner/
    organization/location/healthcareService — there's no existence check to
    run here; the identifier fallback (see PractitionerRoleEndpointInput) is
    often the only populated half."""
    return parse_reference(ref, PractitionerRoleEndpointReferenceType)

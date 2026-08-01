"""
Shared reference-fallback helpers for any resource with a resolved
Reference(Organization) + logical-identifier-fallback field (e.g.
Patient.identifier.assigner, Practitioner.qualification.issuer). Extracted
from patient_repository so Practitioner (and future resources) can reuse the
same pattern instead of re-deriving it.
"""

from app.core.filters import parse_reference
from app.core.reference_resolver import ensure_resource_exists
from app.models.enums import OrganizationReferenceType


def _parse_org_ref(ref: str) -> tuple:
    """Parse 'Organization/123' → (OrganizationReferenceType.Organization, 123)."""
    return parse_reference(ref, OrganizationReferenceType)


_IDENTIFIER_FALLBACK_SUFFIXES = (
    "identifier_use",
    "identifier_type_system",
    "identifier_type_version",
    "identifier_type_code",
    "identifier_type_display",
    "identifier_type_text",
    "identifier_type_user_selected",
    "identifier_system",
    "identifier_value",
    "identifier_period_start",
    "identifier_period_end",
)


def _reference_kwargs(prefix: str, payload) -> dict:
    """Build `{prefix}_identifier_*` ORM constructor kwargs from a payload's
    matching fields — the logical-reference fallback used alongside every
    flattened `{prefix}_type`/`{prefix}_id`/`{prefix}_display` Reference field
    for when the target isn't a resource in this system."""
    return {
        f"{prefix}_{suffix}": getattr(payload, f"{prefix}_{suffix}")
        for suffix in _IDENTIFIER_FALLBACK_SUFFIXES
    }


def _org_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM constructor
    kwargs from a FHIR reference string (e.g. 'Organization/100') — used for
    Reference(Organization) fields expressed as a single string field on the
    payload rather than separate type+id fields."""
    ref_type, ref_id = _parse_org_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


async def _validate_reference(session, org_id, ref_type, ref_id, field_name: str) -> None:
    """Confirms a resolved `type`+`id` reference actually exists, scoped to
    the acting resource's own org_id — the identifier fallback is the
    intended path for anything cross-org/external, so a resolved reference
    can safely assume same-tenant. No-op when either half is absent (nothing
    to check)."""
    if ref_type and ref_id:
        await ensure_resource_exists(
            session, ref_type, ref_id, org_id=org_id, field_name=field_name
        )

from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.schedule import (
    ScheduleIdentifier,
    ScheduleModel,
    ScheduleServiceCategory,
    ScheduleServiceType,
    ScheduleSpecialty,
)
from app.models.schedule.enums import ScheduleActorReferenceType
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
    "_actor_ref_kwargs",
    "_org_ref_kwargs",
    "_parse_actor_ref",
    "_parse_org_ref",
    "_reference_kwargs",
    "_validate_actor_reference",
    "_validate_reference",
    "_with_relationships",
]

# Of FHIR R4's seven allowed Schedule.actor[] target types, only these four
# are modeled resources in this system (registered in RESOURCE_REGISTRY —
# see app/core/reference_resolver.py). Patient/RelatedPerson/Device rows
# always rely on the reference_identifier_* logical-reference fallback
# instead — calling ensure_resource_exists() for an unregistered type fails
# closed (422 on every valid reference to one), so validation is skipped
# for those three the same way HealthcareServiceEndpoint's reference skips
# it entirely (Endpoint isn't modeled either).
_MODELED_ACTOR_TYPES = {
    ScheduleActorReferenceType.Practitioner,
    ScheduleActorReferenceType.PractitionerRole,
    ScheduleActorReferenceType.HealthcareService,
    ScheduleActorReferenceType.Location,
}


# Sortable fields exposed via the `sort` list-query param (see
# app.core.pagination.resolve_sort) — mirrors PractitionerRole's _shared.py.
_SORTABLE_FIELDS = {
    "schedule_id": ScheduleModel.schedule_id,
    "created_at": ScheduleModel.created_at,
    "updated_at": ScheduleModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load all 5 schedule sub-resources to avoid N+1 and async
    lazy-load failures. identifier.type_codings, service_category.codings,
    service_type.codings, and specialty.codings are each a nested 0..*
    coding child table now (see app.models.schedule.*) — mirrors
    app.repository.practitioner_role._shared._with_relationships."""
    return stmt.options(
        selectinload(ScheduleModel.identifiers).selectinload(
            ScheduleIdentifier.type_codings
        ),
        selectinload(ScheduleModel.service_categories).selectinload(
            ScheduleServiceCategory.codings
        ),
        selectinload(ScheduleModel.service_types).selectinload(
            ScheduleServiceType.codings
        ),
        selectinload(ScheduleModel.specialties).selectinload(
            ScheduleSpecialty.codings
        ),
        selectinload(ScheduleModel.actors),
    )


def _parse_actor_ref(ref: str) -> tuple:
    """Parse 'Practitioner/30001' → (ScheduleActorReferenceType.Practitioner, 30001)."""
    return parse_reference(ref, ScheduleActorReferenceType)


def _actor_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM constructor
    kwargs from a FHIR reference string (e.g. 'Practitioner/30001') for the
    Schedule.actor[] polymorphic Reference field."""
    ref_type, ref_id = _parse_actor_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


async def _validate_actor_reference(session, org_id, ref_type, ref_id) -> None:
    """Same as `_validate_reference`, but only actually checks existence for
    the four Schedule.actor[] target types this system models — see
    `_MODELED_ACTOR_TYPES`'s docstring above for why the other three must
    skip validation entirely rather than fail closed."""
    if ref_type in _MODELED_ACTOR_TYPES:
        await _validate_reference(session, org_id, ref_type, ref_id, "actor")

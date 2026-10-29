from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.appointment_response import (
    AppointmentResponseIdentifier,
    AppointmentResponseModel,
    AppointmentResponseParticipantType,
)
from app.models.appointment_response.enums import AppointmentResponseActorReferenceType
from app.models.enums import AppointmentReferenceType
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
    "_appointment_ref_kwargs",
    "_org_ref_kwargs",
    "_parse_actor_ref",
    "_parse_appointment_ref",
    "_parse_org_ref",
    "_reference_kwargs",
    "_validate_actor_reference",
    "_validate_reference",
    "_with_relationships",
]

# Of FHIR R4's seven allowed AppointmentResponse.actor target types, only
# these four are modeled resources in this system (registered in
# RESOURCE_REGISTRY — see app/core/reference_resolver.py). Patient/
# RelatedPerson/Device rows always rely on the reference_identifier_*
# logical-reference fallback instead — calling ensure_resource_exists() for
# an unregistered type fails closed (422 on every valid reference to one),
# so validation is skipped for those three — same reasoning as
# app.repository.appointment._shared._MODELED_PARTICIPANT_ACTOR_TYPES.
_MODELED_ACTOR_TYPES = {
    AppointmentResponseActorReferenceType.Practitioner,
    AppointmentResponseActorReferenceType.PractitionerRole,
    AppointmentResponseActorReferenceType.HealthcareService,
    AppointmentResponseActorReferenceType.Location,
}


# Sortable fields exposed via the `sort` list-query param (see
# app.core.pagination.resolve_sort) — mirrors Appointment's _shared.py.
_SORTABLE_FIELDS = {
    "appointment_response_id": AppointmentResponseModel.appointment_response_id,
    "start": AppointmentResponseModel.start,
    "created_at": AppointmentResponseModel.created_at,
    "updated_at": AppointmentResponseModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load every AppointmentResponse sub-resource to avoid N+1 and
    async lazy-load failures. identifier.type_codings and
    participant_type.codings are each a nested 0..* coding child table —
    mirrors app.repository.appointment._shared._with_relationships."""
    return stmt.options(
        selectinload(AppointmentResponseModel.identifiers).selectinload(
            AppointmentResponseIdentifier.type_codings
        ),
        selectinload(AppointmentResponseModel.participant_types).selectinload(
            AppointmentResponseParticipantType.codings
        ),
    )


def _parse_appointment_ref(ref: str) -> tuple:
    """Parse 'Appointment/40001' → (AppointmentReferenceType.Appointment, 40001)."""
    return parse_reference(ref, AppointmentReferenceType)


def _appointment_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM constructor
    kwargs from a FHIR reference string for the required
    AppointmentResponse.appointment field."""
    ref_type, ref_id = _parse_appointment_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


def _parse_actor_ref(ref: str) -> tuple:
    """Parse 'Practitioner/30001' → (AppointmentResponseActorReferenceType.Practitioner, 30001)."""
    return parse_reference(ref, AppointmentResponseActorReferenceType)


def _actor_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM constructor
    kwargs from a FHIR reference string for the actor polymorphic
    Reference field."""
    ref_type, ref_id = _parse_actor_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


async def _validate_actor_reference(session, org_id, ref_type, ref_id) -> None:
    """Same as `_validate_reference`, but only actually checks existence for
    the four actor target types this system models — see
    `_MODELED_ACTOR_TYPES`'s docstring above."""
    if ref_type in _MODELED_ACTOR_TYPES:
        await _validate_reference(session, org_id, ref_type, ref_id, "actor")

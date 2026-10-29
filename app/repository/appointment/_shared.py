from sqlalchemy.orm import selectinload

from app.core.filters import parse_reference
from app.models.appointment import (
    AppointmentIdentifier,
    AppointmentModel,
    AppointmentParticipant,
    AppointmentParticipantType,
    AppointmentReasonCode,
    AppointmentServiceCategory,
    AppointmentServiceType,
    AppointmentSpecialty,
)
from app.models.appointment.enums import (
    AppointmentBasedOnReferenceType,
    AppointmentParticipantActorReferenceType,
    AppointmentReasonReferenceType,
    AppointmentSlotReferenceType,
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
    "_actor_ref_kwargs",
    "_any_ref_kwargs",
    "_based_on_ref_kwargs",
    "_org_ref_kwargs",
    "_parse_actor_ref",
    "_parse_any_ref",
    "_parse_based_on_ref",
    "_parse_org_ref",
    "_parse_reason_reference_ref",
    "_parse_slot_ref",
    "_reason_reference_ref_kwargs",
    "_reference_kwargs",
    "_slot_ref_kwargs",
    "_validate_actor_reference",
    "_validate_reference",
    "_with_relationships",
]

# Of FHIR R4's seven allowed Appointment.participant.actor target types,
# only these four are modeled resources in this system (registered in
# RESOURCE_REGISTRY — see app/core/reference_resolver.py). Patient/
# RelatedPerson/Device rows always rely on the reference_identifier_*
# logical-reference fallback instead — calling ensure_resource_exists() for
# an unregistered type fails closed (422 on every valid reference to one),
# so validation is skipped for those three — same reasoning as Schedule's
# own _MODELED_ACTOR_TYPES.
_MODELED_PARTICIPANT_ACTOR_TYPES = {
    AppointmentParticipantActorReferenceType.Practitioner,
    AppointmentParticipantActorReferenceType.PractitionerRole,
    AppointmentParticipantActorReferenceType.HealthcareService,
    AppointmentParticipantActorReferenceType.Location,
}


# Sortable fields exposed via the `sort` list-query param (see
# app.core.pagination.resolve_sort) — mirrors Slot's _shared.py.
_SORTABLE_FIELDS = {
    "appointment_id": AppointmentModel.appointment_id,
    "start": AppointmentModel.start,
    "end": AppointmentModel.end,
    "created_at": AppointmentModel.created_at,
    "updated_at": AppointmentModel.updated_at,
}


def _with_relationships(stmt):
    """Eager-load every Appointment sub-resource to avoid N+1 and async
    lazy-load failures. identifier.type_codings, service_category/
    service_type/specialty/reason_code's codings, and
    participant.types.codings are each a nested 0..* coding child table —
    mirrors app.repository.slot._shared._with_relationships."""
    return stmt.options(
        selectinload(AppointmentModel.identifiers).selectinload(
            AppointmentIdentifier.type_codings
        ),
        selectinload(AppointmentModel.service_categories).selectinload(
            AppointmentServiceCategory.codings
        ),
        selectinload(AppointmentModel.service_types).selectinload(
            AppointmentServiceType.codings
        ),
        selectinload(AppointmentModel.specialties).selectinload(
            AppointmentSpecialty.codings
        ),
        selectinload(AppointmentModel.reason_codes).selectinload(
            AppointmentReasonCode.codings
        ),
        selectinload(AppointmentModel.reason_references),
        selectinload(AppointmentModel.supporting_informations),
        selectinload(AppointmentModel.slots),
        selectinload(AppointmentModel.based_ons),
        selectinload(AppointmentModel.participants)
        .selectinload(AppointmentParticipant.types)
        .selectinload(AppointmentParticipantType.codings),
        selectinload(AppointmentModel.requested_periods),
        selectinload(AppointmentModel.cancelation_reason_codings),
        selectinload(AppointmentModel.appointment_type_codings),
    )


def _parse_actor_ref(ref: str) -> tuple:
    """Parse 'Practitioner/30001' → (AppointmentParticipantActorReferenceType.Practitioner, 30001)."""
    return parse_reference(ref, AppointmentParticipantActorReferenceType)


def _actor_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM constructor
    kwargs from a FHIR reference string for the participant.actor polymorphic
    Reference field."""
    ref_type, ref_id = _parse_actor_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


async def _validate_actor_reference(session, org_id, ref_type, ref_id) -> None:
    """Same as `_validate_reference`, but only actually checks existence for
    the four participant.actor target types this system models — see
    `_MODELED_PARTICIPANT_ACTOR_TYPES`'s docstring above."""
    if ref_type in _MODELED_PARTICIPANT_ACTOR_TYPES:
        await _validate_reference(session, org_id, ref_type, ref_id, "actor")


def _parse_any_ref(ref: str) -> tuple[str | None, int | None]:
    """Parse a 'ResourceType/id' string into (type, id) WITHOUT validating
    the type against any enum — used for Appointment.supportingInformation,
    the one genuinely Reference(Any) field on this resource (see
    app.models.appointment.supporting_information's docstring). Never
    raises: an absolute URL, a non-numeric id, or any other shape this
    system doesn't recognize just comes back as (None, None), falling back
    to the raw reference_reference string + identifier fallback instead of
    422-rejecting a structurally valid-but-foreign reference."""
    parts = ref.split("/", 1)
    if len(parts) != 2:
        return None, None
    resource_type, raw_id = parts
    try:
        return resource_type, int(raw_id)
    except ValueError:
        return resource_type, None


def _any_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    """Build `{prefix}_type`/`{prefix}_id`/`{prefix}_display` ORM constructor
    kwargs for Appointment.supportingInformation — `{prefix}_type` is a
    plain free-text string column here, never a Postgres Enum."""
    ref_type, ref_id = _parse_any_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


# reasonReference/basedOn (neither target type is a modeled resource here —
# see each enum's docstring) and slot (Slot IS modeled, so its existence
# check is actually enforced by _validate_reference in full.py) — all three
# still parse through a real Enum (a small, genuinely finite target-type
# set), unlike supportingInformation's free-text Reference(Any) above.


def _parse_reason_reference_ref(ref: str) -> tuple:
    return parse_reference(ref, AppointmentReasonReferenceType)


def _reason_reference_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    ref_type, ref_id = _parse_reason_reference_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


def _parse_slot_ref(ref: str) -> tuple:
    return parse_reference(ref, AppointmentSlotReferenceType)


def _slot_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    ref_type, ref_id = _parse_slot_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }


def _parse_based_on_ref(ref: str) -> tuple:
    return parse_reference(ref, AppointmentBasedOnReferenceType)


def _based_on_ref_kwargs(prefix: str, ref: str | None, display: str | None) -> dict:
    ref_type, ref_id = _parse_based_on_ref(ref) if ref else (None, None)
    return {
        f"{prefix}_type": ref_type,
        f"{prefix}_id": ref_id,
        f"{prefix}_display": display,
    }

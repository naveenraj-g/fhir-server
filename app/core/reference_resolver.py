"""
Generic, resource-type-dynamic existence check for resolved `type`/`id`
Reference pairs (e.g. Patient.generalPractitioner, Patient.link.other) and for
plain resource-ID validation more broadly.

These flattened Reference fields can't have a real DB `ForeignKey` — the
target table varies per row depending on `{prefix}_type` — so nothing
previously confirmed a resolved `{prefix}_id` (the PUBLIC sequence ID, not the
internal PK — see app.fhir.mappers.patient.fhir._fhir_reference) actually
points at a real row. RESOURCE_REGISTRY relies on every resource already
following the same `<resource>_id`/`org_id`/`user_id` column convention (see
CLAUDE.md's Standard Columns), so one dynamic-dispatch function covers any
registered resource type instead of a hand-written check per resource.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.errors.domain import BusinessRuleViolationError
from app.models.appointment import AppointmentModel
from app.models.encounter import EncounterModel
from app.models.healthcare_service import HealthcareServiceModel
from app.models.location import LocationModel
from app.models.medication_request import MedicationRequestModel
from app.models.organization import OrganizationModel
from app.models.practitioner import PractitionerModel
from app.models.practitioner_role import PractitionerRoleModel
from app.models.schedule import ScheduleModel
from app.models.service_request import ServiceRequestModel
from app.models.slot import SlotModel

logger = get_logger(__name__)

# Trimmed down to Organization/Location/HealthcareService/Practitioner/
# PractitionerRole/Schedule only — every other resource was deleted to
# rebuild from scratch; re-register a resource here as soon as something
# needs to reference into it again (e.g. Location.partOf needs its own
# Location entry so the self-referential existence check doesn't fail
# closed).
RESOURCE_REGISTRY: dict[str, tuple[type, str]] = {
    "Organization": (OrganizationModel, "organization_id"),
    # Location.partOf is self-referential, so this entry is what makes the
    # partOf existence check work at all — an unregistered type fails closed
    # (resource_exists returns False), which would 422 every valid partOf.
    # Note Location has no user_id column, so resource_exists' user_id filter
    # must never be passed for it — same as Organization.
    "Location": (LocationModel, "location_id"),
    "HealthcareService": (HealthcareServiceModel, "healthcare_service_id"),
    # Registered so PractitionerRole.practitioner's existence check works —
    # Practitioner has a user_id column (see PractitionerModel's docstring),
    # but resource_exists() only applies that filter when the caller passes
    # user_id, which PractitionerRole's own reference validation never does.
    "Practitioner": (PractitionerModel, "practitioner_id"),
    # Registered so Schedule.actor's existence check works when the actor
    # is a PractitionerRole.
    "PractitionerRole": (PractitionerRoleModel, "practitioner_role_id"),
    # Registered so Slot.schedule's existence check works.
    "Schedule": (ScheduleModel, "schedule_id"),
    # Registered so Appointment.slot's existence check works.
    "Slot": (SlotModel, "slot_id"),
    # Registered so AppointmentResponse.appointment's existence check works.
    "Appointment": (AppointmentModel, "appointment_id"),
    # Encounter.partOf is self-referential, so this entry is what makes
    # that existence check work at all — same reasoning as Location's own
    # self-referential partOf entry above. Also registered so
    # Encounter.appointment's existence check works the other way.
    "Encounter": (EncounterModel, "encounter_id"),
    # ServiceRequest.replaces is self-referential (same reasoning as
    # Location's/Encounter's own self-referential entries above) — also
    # registered so ServiceRequest.basedOn's ServiceRequest subset and
    # ServiceRequest's own org_id/tenant_id-scoped lookups work.
    "ServiceRequest": (ServiceRequestModel, "service_request_id"),
    # MedicationRequest.priorPrescription is self-referential — also
    # registered so MedicationRequest.basedOn's MedicationRequest subset
    # works.
    "MedicationRequest": (MedicationRequestModel, "medication_request_id"),
}


async def resource_exists(
    session: AsyncSession,
    resource_type: str,
    resource_id: int,
    *,
    org_id: str | None = None,
    user_id: str | None = None,
) -> bool:
    """Generic existence check for any resource in RESOURCE_REGISTRY,
    dynamically dispatched by resource_type (e.g. "Organization"). org_id/
    user_id are optional tenant/ownership filters — pass either, both, or
    neither. An unregistered resource_type fails closed (returns False).

    resource_type may be a plain str or a `(str, Enum)` member (every
    resource-reference-type enum in this codebase is one) — normalized via
    `.value` since Python 3.11+ Enum.__format__ no longer defers to the str
    mixin, which would otherwise leak "SomeEnum.Organization" into error
    messages instead of "Organization"."""
    resource_type = getattr(resource_type, "value", resource_type)
    entry = RESOURCE_REGISTRY.get(resource_type)
    if entry is None:
        return False
    model, id_column = entry
    stmt = select(model.id).where(getattr(model, id_column) == resource_id)
    if org_id is not None:
        # Every registered model's tenant-scoping column is org_id, except
        # OrganizationModel — renamed to tenant_id to avoid the column
        # literally being named the same thing as the Organization entity
        # itself (see app/models/shared/tenant_audit.py's docstring).
        org_column = "tenant_id" if hasattr(model, "tenant_id") else "org_id"
        stmt = stmt.where(getattr(model, org_column) == org_id)
    if user_id is not None:
        if not hasattr(model, "user_id"):
            raise ValueError(
                f"{resource_type} has no user_id column — caller must not pass user_id"
            )
        stmt = stmt.where(model.user_id == user_id)
    return (await session.execute(stmt)).scalar_one_or_none() is not None


async def ensure_resource_exists(
    session: AsyncSession,
    resource_type: str,
    resource_id: int,
    *,
    org_id: str | None = None,
    user_id: str | None = None,
    field_name: str | None = None,
) -> None:
    """Raises BusinessRuleViolationError (422) if the reference doesn't
    resolve — the convenience wrapper repository call sites use, so each call
    site is a single line instead of an if/raise repeated everywhere."""
    resource_type = getattr(resource_type, "value", resource_type)
    if not await resource_exists(
        session, resource_type, resource_id, org_id=org_id, user_id=user_id
    ):
        # A real business event: the caller pointed at something that isn't
        # there (or isn't theirs). The 422 tells them; this tells us, with the
        # tenant context attached, which is how you tell "typo'd id" apart
        # from "cross-org reference attempt".
        logger.warning(
            "Reference does not resolve",
            extra={
                "event": "reference.unresolved",
                "resource_type": resource_type,
                "resource_id": resource_id,
                "field": field_name,
                "scoped_org_id": org_id,
                "scoped_user_id": user_id,
            },
        )
        raise BusinessRuleViolationError(
            f"{field_name or resource_type}: referenced {resource_type}/{resource_id} does not exist"
        )

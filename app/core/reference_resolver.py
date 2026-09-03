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
from app.models.healthcare_service import HealthcareServiceModel
from app.models.location import LocationModel
from app.models.organization import OrganizationModel
from app.models.patient import PatientModel
from app.models.practitioner import PractitionerModel
from app.models.practitioner_role import PractitionerRoleModel
from app.models.related_person.related_person import RelatedPersonModel
from app.models.schedule import ScheduleModel

logger = get_logger(__name__)

RESOURCE_REGISTRY: dict[str, tuple[type, str]] = {
    "Organization": (OrganizationModel, "organization_id"),
    "Practitioner": (PractitionerModel, "practitioner_id"),
    "PractitionerRole": (PractitionerRoleModel, "practitioner_role_id"),
    "Patient": (PatientModel, "patient_id"),
    "RelatedPerson": (RelatedPersonModel, "related_person_id"),
    # Location.partOf is self-referential, so this entry is what makes the
    # partOf existence check work at all — an unregistered type fails closed
    # (resource_exists returns False), which would 422 every valid partOf.
    # Note Location has no user_id column, so resource_exists' user_id filter
    # must never be passed for it — same as Organization.
    "Location": (LocationModel, "location_id"),
    "HealthcareService": (HealthcareServiceModel, "healthcare_service_id"),
    # Registered so Schedule.actor (and any future reference into Schedule)
    "Schedule": (ScheduleModel, "schedule_id"),
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
        stmt = stmt.where(model.org_id == org_id)
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

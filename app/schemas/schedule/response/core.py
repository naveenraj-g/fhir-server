from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common.fhir import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRPeriod,
    FHIRReference,
)

from .actor import PlainScheduleActor
from .identifier import PlainScheduleIdentifier
from .service_category import PlainScheduleServiceCategory
from .service_type import PlainScheduleServiceType
from .specialty import PlainScheduleSpecialty

# ── FHIR (camelCase) ────────────────────────────────────────────────────────


class FHIRScheduleSchema(BaseModel):
    resourceType: str = Field("Schedule", description="Always 'Schedule'.")
    id: str = Field(..., description="Public schedule_id as a string.")
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External identifiers for this item."
    )
    active: bool | None = Field(
        None, description="Whether this schedule record is in active use."
    )
    serviceCategory: list[FHIRCodeableConcept] | None = Field(
        None,
        description="A broad categorization of the service that is to be performed during this appointment.",
    )
    serviceType: list[FHIRCodeableConcept] | None = Field(
        None, description="The specific service that is to be performed during this appointment."
    )
    specialty: list[FHIRCodeableConcept] | None = Field(
        None, description="The specialty of a practitioner that would be required to perform the service requested in this appointment."
    )
    actor: list[FHIRReference] | None = Field(
        None,
        description="Resource(s) that availability information is being provided for.",
    )
    planningHorizon: FHIRPeriod | None = Field(
        None,
        description="The period of time that the slots that reference this Schedule resource cover (even if none exist).",
    )
    comment: str | None = Field(
        None,
        description="Comments on the availability to describe any extended information.",
    )


class FHIRScheduleBundleEntry(BaseModel):
    resource: FHIRScheduleSchema


class FHIRScheduleBundle(FHIRBundle):
    entry: list[FHIRScheduleBundleEntry] | None = None


# ── Plain (snake_case) ───────────────────────────────────────────────────────


class PlainScheduleResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public schedule_id.")
    active: bool | None = Field(
        None, description="Whether this schedule record is in active use."
    )
    planning_horizon_start: str | None = Field(
        None, description="Start of the period for which slots should be provided."
    )
    planning_horizon_end: str | None = Field(
        None, description="End of the period for which slots should be provided."
    )
    comment: str | None = Field(
        None, description="Comments on the availability to describe any extended information."
    )
    identifier: list[PlainScheduleIdentifier] | None = Field(
        None, description="External identifiers for this item."
    )
    service_category: list[PlainScheduleServiceCategory] | None = Field(
        None, description="High-level category of service."
    )
    service_type: list[PlainScheduleServiceType] | None = Field(
        None, description="Specific service type(s)."
    )
    specialty: list[PlainScheduleSpecialty] | None = Field(
        None, description="Specialties needed for the appointment."
    )
    actor: list[PlainScheduleActor] | None = Field(
        None, description="Resource(s) this schedule provides availability for."
    )
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded ID of the tenant/account this record is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    created_at: str | None = Field(None, description="When this row was created.")
    updated_at: str | None = Field(None, description="When this row was last updated.")
    created_by: str | None = Field(
        None,
        description="Acting user who created this record, forwarded by the gateway.",
    )
    updated_by: str | None = Field(
        None,
        description="Acting user who last updated this record, forwarded by the gateway.",
    )


class PaginatedScheduleResponse(BaseModel):
    total: int | None = Field(
        None, description="Total matching rows (null when total_mode=none)."
    )
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Number of rows skipped before this page.")
    data: list[PlainScheduleResponse]

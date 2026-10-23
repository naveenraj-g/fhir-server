from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
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
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External identifiers for this item."
    )
    active: bool | None = Field(
        None, description="Whether this schedule record is in active use."
    )
    serviceCategory: list[FHIRCodeableConcept] | None = Field(
        None,
        description="A high-level category of service(s) that could be provided using this schedule.",
    )
    serviceType: list[FHIRCodeableConcept] | None = Field(
        None,
        description="The specific service(s) that could be provided using this schedule.",
    )
    specialty: list[FHIRCodeableConcept] | None = Field(
        None,
        description="The specialty of a practitioner that would be required to perform the service requested in this schedule.",
    )
    actor: list[FHIRReference] | None = Field(
        None, description="The resource(s) this schedule resource is for."
    )
    planningHorizon: FHIRPeriod | None = Field(
        None,
        description="The period of time covered by this schedule's slots.",
    )
    comment: str | None = Field(
        None, description="Comments on the availability."
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
        None, description="Start of the period of time covered by this schedule's slots."
    )
    planning_horizon_end: str | None = Field(
        None, description="End of the period of time covered by this schedule's slots."
    )
    comment: str | None = Field(
        None, description="Comments on the availability."
    )
    identifier: list[PlainScheduleIdentifier] | None = Field(
        None, description="External identifiers for this item."
    )
    service_category: list[PlainScheduleServiceCategory] | None = Field(
        None, description="High-level category of service(s)."
    )
    service_type: list[PlainScheduleServiceType] | None = Field(
        None, description="Specific service(s)."
    )
    specialty: list[PlainScheduleSpecialty] | None = Field(
        None, description="Specialty(ies) required to perform the service."
    )
    actor: list[PlainScheduleActor] | None = Field(
        None, description="The resource(s) this schedule resource is for."
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

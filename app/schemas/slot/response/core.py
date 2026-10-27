from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
    PlainCodingRow,
)

from .identifier import PlainSlotIdentifier
from .service_category import PlainSlotServiceCategory
from .service_type import PlainSlotServiceType
from .specialty import PlainSlotSpecialty

# ── FHIR (camelCase) ────────────────────────────────────────────────────────


class FHIRSlotSchema(BaseModel):
    resourceType: str = Field("Slot", description="Always 'Slot'.")
    id: str = Field(..., description="Public slot_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries. Not yet validated against registered extension definitions.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External identifiers for this item."
    )
    serviceCategory: list[FHIRCodeableConcept] | None = Field(
        None, description="A broad categorization of the service for this slot."
    )
    serviceType: list[FHIRCodeableConcept] | None = Field(
        None, description="The type of appointments that can be booked into this slot."
    )
    specialty: list[FHIRCodeableConcept] | None = Field(
        None,
        description="The specialty of a practitioner that would be required to perform the service requested in this slot.",
    )
    appointmentType: FHIRCodeableConcept | None = Field(
        None,
        description="The style of appointment or patient that may be booked in the slot (not service type).",
    )
    schedule: FHIRReference = Field(
        ..., description="The schedule resource that this slot defines an interval of status information."
    )
    status: str = Field(
        ..., description="busy | free | busy-unavailable | busy-tentative | entered-in-error."
    )
    start: str = Field(..., description="Date/Time that the slot is to begin.")
    end: str = Field(..., description="Date/Time that the slot is to conclude.")
    overbooked: bool | None = Field(
        None,
        description="This slot has already been overbooked, appointments are unlikely to be accepted for this time.",
    )
    comment: str | None = Field(
        None, description="Comments on the slot to describe any extended information."
    )


class FHIRSlotBundleEntry(BaseModel):
    resource: FHIRSlotSchema


class FHIRSlotBundle(FHIRBundle):
    entry: list[FHIRSlotBundleEntry] | None = None


# ── Plain (snake_case) ───────────────────────────────────────────────────────


class PlainSlotResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public slot_id.")
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries.",
    )
    schedule: str | None = Field(
        None,
        description="Resolved FHIR reference to the schedule, e.g. 'Schedule/200001'.",
    )
    schedule_type: str | None = Field(
        None, description="Resolved reference target type (always 'Schedule')."
    )
    schedule_id: int | None = Field(
        None, description="Public schedule_id of the resolved Schedule, if any."
    )
    schedule_display: str | None = Field(
        None, description="Plain text narrative that identifies the schedule."
    )
    schedule_identifier_use: str | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    schedule_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — code system for its type."
    )
    schedule_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type code system."
    )
    schedule_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type."
    )
    schedule_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    schedule_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    schedule_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — whether its type was user-selected."
    )
    schedule_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    schedule_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    schedule_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    schedule_identifier_period_end: str | None = Field(
        None, description="Fallback identifier — end of validity period."
    )
    status: str | None = Field(
        None, description="busy | free | busy-unavailable | busy-tentative | entered-in-error."
    )
    start: str | None = Field(None, description="Date/Time that the slot is to begin.")
    end: str | None = Field(None, description="Date/Time that the slot is to conclude.")
    appointment_type_codings: list[PlainCodingRow] | None = Field(
        None, description="Coding(s) for the style of appointment."
    )
    appointment_type_text: str | None = Field(
        None, description="A human language representation of the appointment type."
    )
    overbooked: bool | None = Field(
        None, description="This slot has already been overbooked."
    )
    comment: str | None = Field(None, description="Comments on the slot.")
    identifier: list[PlainSlotIdentifier] | None = Field(
        None, description="External identifiers for this item."
    )
    service_category: list[PlainSlotServiceCategory] | None = Field(
        None, description="Broad categorization of the service."
    )
    service_type: list[PlainSlotServiceType] | None = Field(
        None, description="Appointment type(s)."
    )
    specialty: list[PlainSlotSpecialty] | None = Field(
        None, description="Specialty(ies) required to perform the service."
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


class PaginatedSlotResponse(BaseModel):
    total: int | None = Field(
        None, description="Total matching rows (null when total_mode=none)."
    )
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Number of rows skipped before this page.")
    data: list[PlainSlotResponse]

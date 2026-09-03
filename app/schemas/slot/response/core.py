from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common.fhir import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRReference,
)

from .identifier import PlainSlotIdentifier
from .service_category import PlainSlotServiceCategory
from .service_type import PlainSlotServiceType
from .specialty import PlainSlotSpecialty

# ── FHIR (camelCase) ────────────────────────────────────────────────────────


class FHIRSlotSchema(BaseModel):
    resourceType: str = Field("Slot", description="Always 'Slot'.")
    id: str = Field(..., description="Public slot_id as a string.")
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External identifiers for this item."
    )
    serviceCategory: list[FHIRCodeableConcept] | None = Field(
        None,
        description="A broad categorization of the service that is to be performed during this appointment.",
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
        description="The style of appointment or patient that has been booked in the slot (not service type).",
    )
    schedule: FHIRReference = Field(
        ..., description="The Schedule resource that this slot defines an interval of status information (1..1)."
    )
    status: str | None = Field(
        None,
        description="busy | free | busy-unavailable | busy-tentative | entered-in-error.",
    )
    start: str | None = Field(None, description="Date/Time the slot begins.")
    end: str | None = Field(None, description="Date/Time the slot concludes.")
    overbooked: bool | None = Field(
        None, description="This slot has already been overbooked."
    )
    comment: str | None = Field(
        None,
        description="Comments on the slot to describe any extended information.",
    )


class FHIRSlotBundleEntry(BaseModel):
    resource: FHIRSlotSchema


class FHIRSlotBundle(FHIRBundle):
    entry: list[FHIRSlotBundleEntry] | None = None


# ── Plain (snake_case) ───────────────────────────────────────────────────────


class PlainSlotResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public slot_id.")

    schedule: str | None = Field(
        None, description="Resolved FHIR reference to the Schedule, e.g. 'Schedule/200001'."
    )
    schedule_type: str | None = Field(None, description="Always 'Schedule'.")
    schedule_id: int | None = Field(None, description="Public id of the referenced Schedule.")
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
        None,
        description="busy | free | busy-unavailable | busy-tentative | entered-in-error.",
    )
    start: str | None = Field(None, description="Date/Time the slot begins.")
    end: str | None = Field(None, description="Date/Time the slot concludes.")
    overbooked: bool | None = Field(
        None, description="This slot has already been overbooked."
    )
    comment: str | None = Field(
        None,
        description="Comments on the slot to describe any extended information.",
    )

    appointment_type_system: str | None = Field(None, description="Code system for appointmentType.")
    appointment_type_version: str | None = Field(None, description="Version of the code system used for appointmentType.")
    appointment_type_code: str | None = Field(None, description="A symbol in syntax defined by the code system.")
    appointment_type_display: str | None = Field(None, description="A representation of the meaning of the code in the system.")
    appointment_type_text: str | None = Field(None, description="A human language representation of the appointment type.")
    appointment_type_user_selected: bool | None = Field(None, description="Indicates that this coding was chosen by a user directly.")

    identifier: list[PlainSlotIdentifier] | None = Field(
        None, description="External identifiers for this item."
    )
    service_category: list[PlainSlotServiceCategory] | None = Field(
        None, description="High-level category of service."
    )
    service_type: list[PlainSlotServiceType] | None = Field(
        None, description="Type(s) of appointment that can be booked."
    )
    specialty: list[PlainSlotSpecialty] | None = Field(
        None, description="Specialties needed for the appointment."
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

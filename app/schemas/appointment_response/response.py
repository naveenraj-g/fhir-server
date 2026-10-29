from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
    PlainCodingRow,
)

# ── FHIR (camelCase) ────────────────────────────────────────────────────────


class FHIRAppointmentResponseSchema(BaseModel):
    resourceType: str = Field("AppointmentResponse", description="Always 'AppointmentResponse'.")
    id: str = Field(..., description="Public appointment_response_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions. Response-only.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(None, description="External identifiers for this item.")
    appointment: FHIRReference = Field(
        ..., description="The appointment that this response is replying to."
    )
    start: str | None = Field(None, description="Date/Time this response was made.")
    end: str | None = Field(None, description="This may be either the same as the appointment start, or different.")
    participantType: list[FHIRCodeableConcept] | None = Field(
        None, description="Role of participant in the appointment."
    )
    actor: FHIRReference | None = Field(
        None, description="Person, Location/HealthcareService or Device that this response is for."
    )
    participantStatus: str = Field(
        ..., description="accepted | declined | tentative | needs-action."
    )
    comment: str | None = Field(None, description="Additional comments about the response.")


class FHIRAppointmentResponseBundleEntry(BaseModel):
    resource: FHIRAppointmentResponseSchema


class FHIRAppointmentResponseBundle(FHIRBundle):
    entry: list[FHIRAppointmentResponseBundleEntry] | None = None


# ── Plain (snake_case) ───────────────────────────────────────────────────────


class PlainAppointmentResponseIdentifier(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    use: str | None = None
    type_codings: list[PlainCodingRow] | None = None
    type_text: str | None = None
    system: str | None = None
    value: str | None = None
    period_start: str | None = None
    period_end: str | None = None
    assigner: str | None = None
    assigner_type: str | None = None
    assigner_id: int | None = None
    assigner_display: str | None = None


class PlainAppointmentResponseParticipantType(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    codings: list[PlainCodingRow] | None = None
    text: str | None = None


class PlainAppointmentResponseResponse(BaseModel):
    """Plain snake_case AppointmentResponse representation — named
    "...ResponseResponse" because the FHIR resource itself is named
    AppointmentResponse (this is the response *body*, following the same
    Plain<Resource>Response naming as every other resource)."""

    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public appointment_response_id.")
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries."
    )
    appointment: str | None = Field(
        None, description="Resolved FHIR reference to the appointment, e.g. 'Appointment/40001'."
    )
    appointment_type: str | None = Field(None, description="Resolved reference target type (always 'Appointment').")
    appointment_id: int | None = Field(None, description="Public appointment_id of the resolved Appointment, if any.")
    appointment_display: str | None = Field(None, description="Plain text narrative for the appointment.")
    appointment_identifier_use: str | None = Field(None, description="Fallback identifier — its purpose, if known.")
    appointment_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    appointment_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    appointment_identifier_type_code: str | None = Field(None, description="Fallback identifier — code for its type.")
    appointment_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    appointment_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    appointment_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether its type was user-selected.")
    appointment_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    appointment_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    appointment_identifier_period_start: str | None = Field(None, description="Fallback identifier — start of validity period.")
    appointment_identifier_period_end: str | None = Field(None, description="Fallback identifier — end of validity period.")
    start: str | None = Field(None, description="Date/Time this response was made.")
    end: str | None = Field(None, description="This may be either the same as the appointment start, or different.")
    actor: str | None = Field(None, description="Resolved FHIR reference to the actor, if any.")
    actor_type: str | None = Field(None, description="Resolved reference target type for the actor.")
    actor_id: int | None = Field(None, description="Public id of the resolved actor, if any.")
    actor_display: str | None = Field(None, description="Plain text narrative for the actor.")
    actor_identifier_use: str | None = Field(None, description="Fallback identifier — its purpose, if known.")
    actor_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    actor_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    actor_identifier_type_code: str | None = Field(None, description="Fallback identifier — code for its type.")
    actor_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    actor_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    actor_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether its type was user-selected.")
    actor_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    actor_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    actor_identifier_period_start: str | None = Field(None, description="Fallback identifier — start of validity period.")
    actor_identifier_period_end: str | None = Field(None, description="Fallback identifier — end of validity period.")
    participant_status: str | None = Field(None, description="accepted | declined | tentative | needs-action.")
    comment: str | None = Field(None, description="Additional comments about the response.")
    identifier: list[PlainAppointmentResponseIdentifier] | None = Field(None, description="External identifiers.")
    participant_type: list[PlainAppointmentResponseParticipantType] | None = Field(
        None, description="Role(s) of participant."
    )
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded ID of the tenant/account this record is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    created_at: str | None = Field(None, description="When this row was created.")
    updated_at: str | None = Field(None, description="When this row was last updated.")
    created_by: str | None = Field(None, description="Acting user who created this record, forwarded by the gateway.")
    updated_by: str | None = Field(None, description="Acting user who last updated this record, forwarded by the gateway.")


class PaginatedAppointmentResponseResponse(BaseModel):
    total: int | None = Field(None, description="Total matching rows (null when total_mode=none).")
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Number of rows skipped before this page.")
    data: list[PlainAppointmentResponseResponse]

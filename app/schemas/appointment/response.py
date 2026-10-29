from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
    PlainCodingRow,
)

# ── FHIR (camelCase) ────────────────────────────────────────────────────────


class FHIRAppointmentParticipant(BaseModel):
    type: list[FHIRCodeableConcept] | None = Field(
        None, description="Role of participant in the appointment."
    )
    actor: FHIRReference | None = Field(None, description="Person, Location/HealthcareService or Device.")
    required: str | None = Field(None, description="required | optional | information-only.")
    status: str = Field(..., description="accepted | declined | tentative | needs-action.")
    period: FHIRPeriod | None = Field(None, description="Participation period of the actor.")


class FHIRAppointmentSchema(BaseModel):
    resourceType: str = Field("Appointment", description="Always 'Appointment'.")
    id: str = Field(..., description="Public appointment_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions. Response-only.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(None, description="External identifiers for this item.")
    status: str = Field(
        ...,
        description="proposed | pending | booked | arrived | fulfilled | cancelled | noshow | entered-in-error | checked-in | waitlist.",
    )
    cancelationReason: FHIRCodeableConcept | None = Field(
        None, description="The coded reason for the appointment being cancelled."
    )
    serviceCategory: list[FHIRCodeableConcept] | None = Field(
        None, description="A broad categorization of the service."
    )
    serviceType: list[FHIRCodeableConcept] | None = Field(
        None, description="The specific service to be performed."
    )
    specialty: list[FHIRCodeableConcept] | None = Field(
        None, description="The specialty of a practitioner required for the service."
    )
    appointmentType: FHIRCodeableConcept | None = Field(
        None, description="The style of appointment or patient that may be booked."
    )
    reasonCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Coded reason this appointment is scheduled."
    )
    reasonReference: list[FHIRReference] | None = Field(
        None, description="Reason the appointment is to take place (resource reference)."
    )
    priority: int | None = Field(None, description="The priority of the appointment.")
    description: str | None = Field(None, description="Shown on a subject line in a meeting request.")
    supportingInformation: list[FHIRReference] | None = Field(
        None, description="Additional information to support the appointment."
    )
    start: str | None = Field(None, description="Date/Time that the appointment is to take place.")
    end: str | None = Field(None, description="Date/Time that the appointment is to conclude.")
    minutesDuration: int | None = Field(None, description="Number of minutes the appointment is to take.")
    slot: list[FHIRReference] | None = Field(
        None, description="The slots that will be filled by the appointment."
    )
    created: str | None = Field(None, description="The date this appointment was initially created.")
    comment: str | None = Field(None, description="Additional comments about the appointment.")
    patientInstruction: str | None = Field(None, description="Detailed instructions for the patient.")
    basedOn: list[FHIRReference] | None = Field(
        None, description="The service request this appointment is allocated to assess."
    )
    participant: list[FHIRAppointmentParticipant] = Field(
        ..., description="Participants involved in the appointment, and their role in it."
    )
    requestedPeriod: list[FHIRPeriod] | None = Field(
        None, description="Potential date/time interval(s) requested to allocate the appointment within."
    )


class FHIRAppointmentBundleEntry(BaseModel):
    resource: FHIRAppointmentSchema


class FHIRAppointmentBundle(FHIRBundle):
    entry: list[FHIRAppointmentBundleEntry] | None = None


# ── Plain (snake_case) ───────────────────────────────────────────────────────


class PlainAppointmentIdentifier(BaseModel):
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


class _PlainCodeableConceptRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    codings: list[PlainCodingRow] | None = None
    text: str | None = None


class PlainAppointmentServiceCategory(_PlainCodeableConceptRow):
    pass


class PlainAppointmentServiceType(_PlainCodeableConceptRow):
    pass


class PlainAppointmentSpecialty(_PlainCodeableConceptRow):
    pass


class PlainAppointmentReasonCode(_PlainCodeableConceptRow):
    pass


class _PlainReferenceRow(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    reference: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    reference_display: str | None = None


class PlainAppointmentReasonReference(_PlainReferenceRow):
    pass


class PlainAppointmentSupportingInformation(_PlainReferenceRow):
    pass


class PlainAppointmentSlot(_PlainReferenceRow):
    pass


class PlainAppointmentBasedOn(_PlainReferenceRow):
    pass


class PlainAppointmentRequestedPeriod(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    start: str | None = None
    end: str | None = None


class PlainAppointmentParticipantType(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    codings: list[PlainCodingRow] | None = None
    text: str | None = None


class PlainAppointmentParticipant(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int
    types: list[PlainAppointmentParticipantType] | None = None
    actor: str | None = None
    actor_type: str | None = None
    actor_id: int | None = None
    actor_display: str | None = None
    required: str | None = None
    status: str | None = None
    period_start: str | None = None
    period_end: str | None = None


class PlainAppointmentResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public appointment_id.")
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries."
    )
    status: str | None = Field(
        None,
        description="proposed | pending | booked | arrived | fulfilled | cancelled | noshow | entered-in-error | checked-in | waitlist.",
    )
    cancelation_reason_codings: list[PlainCodingRow] | None = Field(
        None, description="Coding(s) for the cancellation reason."
    )
    cancelation_reason_text: str | None = Field(None, description="Human language cancellation reason.")
    appointment_type_codings: list[PlainCodingRow] | None = Field(
        None, description="Coding(s) for the style of appointment."
    )
    appointment_type_text: str | None = Field(None, description="Human language appointment type.")
    priority: int | None = Field(None, description="The priority of the appointment.")
    description: str | None = Field(None, description="Shown on a subject line in a meeting request.")
    start: str | None = Field(None, description="Date/Time that the appointment is to take place.")
    end: str | None = Field(None, description="Date/Time that the appointment is to conclude.")
    minutes_duration: int | None = Field(None, description="Number of minutes the appointment is to take.")
    created: str | None = Field(None, description="The date this appointment was initially created.")
    comment: str | None = Field(None, description="Additional comments about the appointment.")
    patient_instruction: str | None = Field(None, description="Detailed instructions for the patient.")
    identifier: list[PlainAppointmentIdentifier] | None = Field(None, description="External identifiers.")
    service_category: list[PlainAppointmentServiceCategory] | None = Field(None, description="Broad categorization of the service.")
    service_type: list[PlainAppointmentServiceType] | None = Field(None, description="Specific service(s).")
    specialty: list[PlainAppointmentSpecialty] | None = Field(None, description="Specialty(ies) required.")
    reason_code: list[PlainAppointmentReasonCode] | None = Field(None, description="Coded reason(s).")
    reason_reference: list[PlainAppointmentReasonReference] | None = Field(None, description="Reason reference(s).")
    supporting_information: list[PlainAppointmentSupportingInformation] | None = Field(None, description="Supporting information.")
    slot: list[PlainAppointmentSlot] | None = Field(None, description="Slot(s) filled by the appointment.")
    based_on: list[PlainAppointmentBasedOn] | None = Field(None, description="Based-on reference(s).")
    requested_period: list[PlainAppointmentRequestedPeriod] | None = Field(None, description="Requested period(s).")
    participant: list[PlainAppointmentParticipant] = Field(..., description="Participant(s).")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded ID of the tenant/account this record is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    created_at: str | None = Field(None, description="When this row was created.")
    updated_at: str | None = Field(None, description="When this row was last updated.")
    created_by: str | None = Field(None, description="Acting user who created this record, forwarded by the gateway.")
    updated_by: str | None = Field(None, description="Acting user who last updated this record, forwarded by the gateway.")


class PaginatedAppointmentResponse(BaseModel):
    total: int | None = Field(None, description="Total matching rows (null when total_mode=none).")
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Number of rows skipped before this page.")
    data: list[PlainAppointmentResponse]

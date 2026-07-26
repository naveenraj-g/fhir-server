from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.appointment.enums import (
    AppointmentParticipantRequired,
    AppointmentParticipantStatus,
    AppointmentStatus,
)


class AppointmentIdentifierInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    use: Optional[str] = None
    type_system: Optional[str] = None
    type_code: Optional[str] = None
    type_display: Optional[str] = None
    type_text: Optional[str] = None
    system: Optional[str] = None
    value: Optional[str] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    assigner: Optional[str] = None


class AppointmentServiceCategoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class AppointmentServiceTypeInput(BaseModel):
    """serviceType[] (0..*) CodeableConcept."""
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class AppointmentSpecialtyInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class AppointmentReasonCodeInput(BaseModel):
    """reasonCode[] (0..*) CodeableConcept."""
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class AppointmentReasonReferenceInput(BaseModel):
    """reasonReference[] (0..*) Reference(Condition|Procedure|Observation|ImmunizationRecommendation)."""
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="FHIR reference e.g. 'Condition/120001'.")
    reference_display: Optional[str] = None


class AppointmentSupportingInformationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(
        ...,
        description="FHIR reference to any supporting resource, e.g. 'DocumentReference/456'.",
    )
    reference_display: Optional[str] = None


class AppointmentSlotInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(..., description="FHIR reference, e.g. 'Slot/501'.")
    reference_display: Optional[str] = None


class AppointmentBasedOnInput(BaseModel):
    """basedOn[] (0..*) Reference(ServiceRequest)."""
    model_config = ConfigDict(extra="forbid")
    reference: str = Field(
        ...,
        description="FHIR reference e.g. 'ServiceRequest/80001'.",
    )
    reference_display: Optional[str] = None


class AppointmentParticipantTypeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    coding_system: Optional[str] = None
    coding_code: Optional[str] = None
    coding_display: Optional[str] = None
    text: Optional[str] = None


class AppointmentParticipantInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reference: Optional[str] = Field(
        None,
        description="FHIR reference using the public resource ID, e.g. 'Practitioner/30001' or 'Patient/10001'.",
    )
    reference_display: Optional[str] = None
    types: Optional[List[AppointmentParticipantTypeInput]] = Field(
        None,
        description="Participant role code(s), e.g. [{coding_code: 'ATND', coding_display: 'attender'}].",
    )
    required: Optional[AppointmentParticipantRequired] = Field(
        None, description="required|optional|information-only"
    )
    status: AppointmentParticipantStatus = Field(
        AppointmentParticipantStatus.needs_action,
        description="Participation acceptance status.",
    )
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


class AppointmentRequestedPeriodInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None


# ── Recurrence template (operational, not FHIR R4/R5 standard) ───────────────


class RecurrenceWeeklyTemplateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    monday: Optional[bool] = None
    tuesday: Optional[bool] = None
    wednesday: Optional[bool] = None
    thursday: Optional[bool] = None
    friday: Optional[bool] = None
    saturday: Optional[bool] = None
    sunday: Optional[bool] = None
    week_interval: Optional[int] = Field(None, ge=1, description="Weeks between occurrences.")


class RecurrenceMonthlyTemplateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    day_of_month: Optional[int] = Field(None, ge=1, le=31)
    nth_week_code: Optional[str] = Field(None, description="e.g. '1' (1st week) or '-1' (last week).")
    nth_week_display: Optional[str] = None
    day_of_week_code: Optional[str] = Field(None, description="mon | tue | wed | thu | fri | sat | sun")
    day_of_week_display: Optional[str] = None
    month_interval: int = Field(..., ge=1, description="Months between occurrences.")


class RecurrenceYearlyTemplateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    year_interval: int = Field(..., ge=1, description="Years between occurrences.")


class RecurrenceTemplateInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recurrence_type_code: str = Field(..., description="daily | weekly | monthly | yearly", examples=["weekly"])
    recurrence_type_display: Optional[str] = None
    recurrence_type_system: Optional[str] = None
    timezone_code: Optional[str] = Field(None, description="IANA timezone, e.g. 'America/New_York'.")
    timezone_display: Optional[str] = None
    last_occurrence_date: Optional[date] = Field(None, description="Date after which no more occurrences.")
    occurrence_count: Optional[int] = Field(None, ge=1, description="Total number of occurrences.")
    occurrence_dates: Optional[List[date]] = Field(None, description="Explicit list of occurrence dates.")
    excluding_dates: Optional[List[date]] = Field(None, description="Dates within the series to skip.")
    excluding_recurrence_ids: Optional[List[int]] = Field(None, description="Ordinal occurrence positions to skip.")
    weekly_template: Optional[RecurrenceWeeklyTemplateInput] = None
    monthly_template: Optional[RecurrenceMonthlyTemplateInput] = None
    yearly_template: Optional[RecurrenceYearlyTemplateInput] = None


# ── Create / Patch ────────────────────────────────────────────────────────────


class AppointmentCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "user_id": "user-uuid-123",
                "org_id": "org-uuid-456",
                "status": "booked",
                "start": "2026-06-01T09:00:00Z",
                "end": "2026-06-01T09:30:00Z",
                "minutes_duration": 30,
                "description": "Follow-up visit for hypertension management",
                "comment": "Patient prefers morning appointments.",
                "priority": 5,
                "service_type": [{"coding_code": "57", "coding_display": "Immunisation"}],
                "specialty": [{"coding_code": "394814009", "coding_display": "General practice"}],
                "reason_code": [{"coding_code": "274640006", "coding_display": "Fever"}],
                "participant": [
                    {
                        "reference": "Patient/10001",
                        "reference_display": "John Doe",
                        "required": "required",
                        "status": "accepted",
                    },
                    {
                        "reference": "Practitioner/30001",
                        "reference_display": "Dr. Smith",
                        "types": [{"coding_code": "ATND", "coding_display": "attender"}],
                        "required": "required",
                        "status": "accepted",
                    },
                ],
            }
        },
    )

    user_id: Optional[str] = None
    org_id: Optional[str] = None
    created_by: Optional[str] = None

    status: AppointmentStatus

    # cancelationReason (0..1 CodeableConcept) — R4 spelling
    cancelation_reason_system: Optional[str] = None
    cancelation_reason_code: Optional[str] = None
    cancelation_reason_display: Optional[str] = None
    cancelation_reason_text: Optional[str] = None

    # appointmentType (0..1 CodeableConcept)
    appointment_type_system: Optional[str] = None
    appointment_type_code: Optional[str] = None
    appointment_type_display: Optional[str] = None
    appointment_type_text: Optional[str] = None

    # priority (0..1 unsignedInt)
    priority: Optional[int] = Field(None, ge=0)

    # scheduling
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    minutes_duration: Optional[int] = Field(None, ge=1)
    created: Optional[datetime] = Field(None, description="When this appointment was initially created.")

    # descriptive
    description: Optional[str] = None
    comment: Optional[str] = None
    patient_instruction: Optional[str] = None

    # sub-resources (arrays)
    identifier: Optional[List[AppointmentIdentifierInput]] = None
    service_category: Optional[List[AppointmentServiceCategoryInput]] = None
    service_type: Optional[List[AppointmentServiceTypeInput]] = None
    specialty: Optional[List[AppointmentSpecialtyInput]] = None
    reason_code: Optional[List[AppointmentReasonCodeInput]] = None
    reason_reference: Optional[List[AppointmentReasonReferenceInput]] = None
    supporting_information: Optional[List[AppointmentSupportingInformationInput]] = None
    slot: Optional[List[AppointmentSlotInput]] = None
    based_on: Optional[List[AppointmentBasedOnInput]] = None
    participant: List[AppointmentParticipantInput] = Field(..., min_length=1)
    requested_period: Optional[List[AppointmentRequestedPeriodInput]] = None
    recurrence_template: Optional[RecurrenceTemplateInput] = None


class AppointmentPatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Optional[AppointmentStatus] = None
    cancelation_reason_system: Optional[str] = None
    cancelation_reason_code: Optional[str] = None
    cancelation_reason_display: Optional[str] = None
    cancelation_reason_text: Optional[str] = None
    priority: Optional[int] = Field(None, ge=0)
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    minutes_duration: Optional[int] = Field(None, ge=1)
    description: Optional[str] = None
    comment: Optional[str] = None
    patient_instruction: Optional[str] = None
    updated_by: Optional[str] = None

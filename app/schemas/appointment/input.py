from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput
from app.schemas.enums import (
    AppointmentParticipantRequired,
    AppointmentParticipationStatus,
    AppointmentStatus,
    IdentifierUse,
)

# ---------------------------------------------------------------------------
# Sub-resource list item schemas
# ---------------------------------------------------------------------------


class AppointmentIdentifierInput(BaseModel):
    """identifier[] — mirrors app.schemas.slot.input.identifier.SlotIdentifierInput."""

    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = Field(
        None,
        description="Identifies the purpose for this identifier, if known — usual|official|temp|secondary|old.",
    )
    type_coding: list[CodingInput] | None = Field(
        None, description="Coding(s) for this identifier's type."
    )
    type_text: str | None = Field(
        None, description="A human language representation of the identifier's type."
    )
    system: str | None = Field(None, description="Establishes the namespace for the value.")
    value: str | None = Field(
        None,
        description="The portion of the identifier typically relevant to the user and which is unique within the system.",
    )
    period_start: datetime | None = Field(
        None, description="Start of the time period during which this identifier is/was valid for use."
    )
    period_end: datetime | None = Field(
        None, description="End of the time period during which this identifier is/was valid for use."
    )
    assigner: str | None = Field(
        None,
        description="Organization that issued/manages this identifier, as a FHIR reference string (e.g. 'Organization/190001').",
    )
    assigner_display: str | None = Field(
        None, description="Plain text narrative that identifies the assigning organization in addition to the reference."
    )
    assigner_identifier_use: IdentifierUse | None = Field(
        None, description="Logical-identifier fallback for the assigner — identifies its purpose, if known."
    )
    assigner_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    assigner_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    assigner_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    assigner_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    assigner_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    assigner_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether its type was user-selected.")
    assigner_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    assigner_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    assigner_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    assigner_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")


class _CodeableConceptListInput(BaseModel):
    """Shared shape for every 0..* CodeableConcept list field on Appointment
    (serviceCategory/serviceType/specialty/reasonCode) — `coding` is the
    real 0..* child table, `text` is its flattened sibling. Subclassed per
    field purely so each has its own class name for clarity in the
    create/patch schemas below — same convention as Slot's own
    Service*/Specialty inputs, which do the same thing one file each."""

    model_config = ConfigDict(extra="forbid")
    coding: list[CodingInput] | None = Field(None, description="Coding(s) for this concept.")
    text: str | None = Field(None, description="A human language representation of the concept.")


class AppointmentServiceCategoryInput(_CodeableConceptListInput):
    """serviceCategory[] — a broad categorization of the service."""


class AppointmentServiceTypeInput(_CodeableConceptListInput):
    """serviceType[] — the specific service to be performed."""


class AppointmentSpecialtyInput(_CodeableConceptListInput):
    """specialty[] — the specialty of a practitioner required for the service."""


class AppointmentReasonCodeInput(_CodeableConceptListInput):
    """reasonCode[] — the coded reason for the appointment."""


class _ReferenceListInput(BaseModel):
    """Shared shape for every 0..* Reference list field on Appointment that
    is itself a bare reference (reasonReference/supportingInformation/slot/
    basedOn) — the field prefix is `reference` (not `actor`/`assigner`),
    since the whole object IS the reference. Mirrors
    app.schemas.schedule.input.actor.ScheduleActorInput's shape, applied to
    a 0..* list instead of a single 0..1 field."""

    model_config = ConfigDict(extra="forbid")
    reference: str | None = Field(None, description="FHIR reference string, e.g. 'Slot/220001'.")
    reference_display: str | None = Field(
        None, description="Plain text narrative that identifies the target in addition to the reference."
    )
    reference_identifier_use: IdentifierUse | None = Field(
        None, description="Logical-identifier fallback (used when there's no resolvable reference) — identifies its purpose, if known."
    )
    reference_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    reference_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    reference_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    reference_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    reference_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    reference_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether its type was user-selected.")
    reference_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    reference_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    reference_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    reference_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")


class AppointmentReasonReferenceInput(_ReferenceListInput):
    """reasonReference[] — Reference(Condition|Procedure|Observation|ImmunizationRecommendation).
    None of these are modeled resources in this system — see
    app.models.appointment.enums.AppointmentReasonReferenceType's docstring."""


class AppointmentSupportingInformationInput(_ReferenceListInput):
    """supportingInformation[] — Reference(Any). Target type is never
    validated against an enum — see
    app.models.appointment.supporting_information's docstring."""


class AppointmentSlotInput(_ReferenceListInput):
    """slot[] — Reference(Slot). Slot IS a modeled resource; rejected with
    422 if it doesn't exist in this org."""


class AppointmentBasedOnInput(_ReferenceListInput):
    """basedOn[] — Reference(ServiceRequest). Not a modeled resource in
    this system."""


class AppointmentRequestedPeriodInput(BaseModel):
    """requestedPeriod[] — potential date/time interval(s) requested to
    allocate the appointment within."""

    model_config = ConfigDict(extra="forbid")
    start: datetime | None = Field(None, description="Start of the requested period.")
    end: datetime | None = Field(None, description="End of the requested period.")


class AppointmentParticipantTypeInput(BaseModel):
    """One entry of participant.type[] (0..* CodeableConcept) — the role
    this participant plays (e.g. 'attender', 'translator')."""

    model_config = ConfigDict(extra="forbid")
    coding: list[CodingInput] | None = Field(None, description="Coding(s) for this participant role.")
    text: str | None = Field(None, description="A human language representation of the role.")


class AppointmentParticipantInput(BaseModel):
    """participant[] — participants involved in the appointment, and their
    role in it. `actor` is polymorphic across 7 possible target types — see
    app.models.appointment.enums.AppointmentParticipantActorReferenceType's
    docstring for which are modeled resources here. `status` is 1..1
    required; `required` is 0..1."""

    model_config = ConfigDict(extra="forbid")
    type: list[AppointmentParticipantTypeInput] | None = Field(
        None, description="Role of participant in the appointment."
    )
    actor: str | None = Field(
        None,
        description="FHIR reference string to the participant, e.g. 'Practitioner/30001' or 'Location/230001'.",
    )
    actor_display: str | None = Field(
        None, description="Plain text narrative that identifies the actor in addition to the reference."
    )
    actor_identifier_use: IdentifierUse | None = Field(
        None, description="Logical-identifier fallback (used when there's no resolvable reference) — identifies its purpose, if known."
    )
    actor_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    actor_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    actor_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    actor_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    actor_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    actor_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether its type was user-selected.")
    actor_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    actor_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    actor_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    actor_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")
    required: AppointmentParticipantRequired | None = Field(
        None, description="required | optional | information-only."
    )
    status: AppointmentParticipationStatus = Field(
        ..., description="accepted | declined | tentative | needs-action."
    )
    period_start: datetime | None = Field(None, description="Start of participation period.")
    period_end: datetime | None = Field(None, description="End of participation period.")


# ---------------------------------------------------------------------------
# Create / Patch
# ---------------------------------------------------------------------------


class AppointmentCreateSchema(BaseModel):
    """Creates an Appointment and any combination of its sub-resource lists
    atomically in one request — same set-once-then-patch shape as
    Organization/HealthcareService/PractitionerRole/Schedule/Slot, no
    separate scalar-only vs. full create split. tenant_id and created_by
    both come from the verified JWT (actor.org_id / actor.sub) — neither is
    a request body field. Like Organization/Location/HealthcareService/
    PractitionerRole/Schedule/Slot, Appointment has no user_id field at
    all — it's a shared tenant-level entity (any participant may need to
    see it), not scoped to an individual end-user.

    `cancelation_reason`/`appointment_type` are each a 0..1 CodeableConcept
    living directly on this schema (not a list sub-resource) —
    `*_coding` is the real 0..* coding list, `*_text` is the
    CodeableConcept's own sibling field. `participant` is 1..* per spec but
    modeled as 0..* here (enforced by the FHIR validator layer, not
    Pydantic) — same as Schedule.actor.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "booked",
                "description": "Follow-up consultation",
                "start": "2026-02-01T09:00:00Z",
                "end": "2026-02-01T09:30:00Z",
                "minutes_duration": 30,
                "comment": "Routine follow-up",
                "participant": [
                    {
                        "actor": "Practitioner/30001",
                        "required": "required",
                        "status": "accepted",
                    },
                    {
                        "actor": "Location/230001",
                        "required": "optional",
                        "status": "accepted",
                    },
                ],
                "identifier": [],
                "service_category": [],
                "service_type": [{"coding": [{"code": "57", "display": "Immunization"}]}],
                "specialty": [],
                "reason_code": [],
                "reason_reference": [],
                "supporting_information": [],
                "slot": [],
                "based_on": [],
                "requested_period": [],
            }
        },
    )

    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries. Not yet validated against registered extension definitions.",
    )

    # status (1..1) — required
    status: AppointmentStatus = Field(
        ...,
        description="proposed | pending | booked | arrived | fulfilled | cancelled | noshow | entered-in-error | checked-in | waitlist.",
    )

    cancelation_reason_coding: list[CodingInput] | None = Field(
        None, description="Coding(s) for the reason the appointment was cancelled."
    )
    cancelation_reason_text: str | None = Field(
        None, description="A human language representation of the cancellation reason."
    )

    appointment_type_coding: list[CodingInput] | None = Field(
        None, description="Coding(s) for the style of appointment or patient that may be booked."
    )
    appointment_type_text: str | None = Field(
        None, description="A human language representation of the appointment type."
    )

    priority: int | None = Field(
        None, ge=0, description="The priority of the appointment — higher values indicate higher priority."
    )
    description: str | None = Field(
        None, description="Shown on a subject line in a meeting request, or appointment list."
    )
    start: datetime | None = Field(None, description="Date/Time that the appointment is to take place.")
    end: datetime | None = Field(None, description="Date/Time that the appointment is to conclude.")
    minutes_duration: int | None = Field(
        None, gt=0, description="Number of minutes that the appointment is to take."
    )
    created: datetime | None = Field(
        None, description="The date that this appointment was initially created."
    )
    comment: str | None = Field(
        None, description="Additional comments about the appointment."
    )
    patient_instruction: str | None = Field(
        None, description="Detailed information and instructions for the patient."
    )

    identifier: list[AppointmentIdentifierInput] | None = Field(
        None, description="External identifiers for this item."
    )
    service_category: list[AppointmentServiceCategoryInput] | None = Field(
        None, description="A broad categorization of the service."
    )
    service_type: list[AppointmentServiceTypeInput] | None = Field(
        None, description="The specific service to be performed."
    )
    specialty: list[AppointmentSpecialtyInput] | None = Field(
        None, description="The specialty of a practitioner required for the service."
    )
    reason_code: list[AppointmentReasonCodeInput] | None = Field(
        None, description="Coded reason this appointment is scheduled."
    )
    reason_reference: list[AppointmentReasonReferenceInput] | None = Field(
        None, description="Reason the appointment is to take place (resource reference)."
    )
    supporting_information: list[AppointmentSupportingInformationInput] | None = Field(
        None, description="Additional information to support the appointment."
    )
    slot: list[AppointmentSlotInput] | None = Field(
        None, description="The slots from the participants' schedules that will be filled by the appointment."
    )
    based_on: list[AppointmentBasedOnInput] | None = Field(
        None, description="The service request this appointment is allocated to assess."
    )
    requested_period: list[AppointmentRequestedPeriodInput] | None = Field(
        None, description="Potential date/time interval(s) requested to allocate the appointment within."
    )
    participant: list[AppointmentParticipantInput] | None = Field(
        None, description="Participants involved in the appointment, and their role in it. 1..* per spec."
    )


class AppointmentPatchSchema(BaseModel):
    """Partial update — only supplied fields are written. Every supplied
    sub-resource list (even `[]`) replaces the corresponding rows wholesale;
    omitted lists are left untouched. updated_by comes from the verified
    JWT (actor.sub), not a request body field."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "fulfilled",
                "comment": "Patient seen, consultation complete",
            }
        },
    )

    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries — replaces the full list if supplied.",
    )
    status: AppointmentStatus | None = Field(
        None,
        description="proposed | pending | booked | arrived | fulfilled | cancelled | noshow | entered-in-error | checked-in | waitlist.",
    )
    cancelation_reason_coding: list[CodingInput] | None = Field(
        None, description="Coding(s) for the cancellation reason — replaces the full list if supplied."
    )
    cancelation_reason_text: str | None = Field(
        None, description="A human language representation of the cancellation reason."
    )
    appointment_type_coding: list[CodingInput] | None = Field(
        None, description="Coding(s) for the style of appointment — replaces the full list if supplied."
    )
    appointment_type_text: str | None = Field(
        None, description="A human language representation of the appointment type."
    )
    priority: int | None = Field(None, ge=0, description="The priority of the appointment.")
    description: str | None = Field(None, description="Shown on a subject line in a meeting request.")
    start: datetime | None = Field(None, description="Date/Time that the appointment is to take place.")
    end: datetime | None = Field(None, description="Date/Time that the appointment is to conclude.")
    minutes_duration: int | None = Field(None, gt=0, description="Number of minutes the appointment is to take.")
    created: datetime | None = Field(None, description="The date this appointment was initially created.")
    comment: str | None = Field(None, description="Additional comments about the appointment.")
    patient_instruction: str | None = Field(None, description="Detailed instructions for the patient.")

    identifier: list[AppointmentIdentifierInput] | None = Field(
        None, description="External identifiers — replaces the full list if supplied."
    )
    service_category: list[AppointmentServiceCategoryInput] | None = Field(
        None, description="Broad categorization of the service — replaces the full list if supplied."
    )
    service_type: list[AppointmentServiceTypeInput] | None = Field(
        None, description="Specific service(s) — replaces the full list if supplied."
    )
    specialty: list[AppointmentSpecialtyInput] | None = Field(
        None, description="Specialty(ies) — replaces the full list if supplied."
    )
    reason_code: list[AppointmentReasonCodeInput] | None = Field(
        None, description="Coded reason(s) — replaces the full list if supplied."
    )
    reason_reference: list[AppointmentReasonReferenceInput] | None = Field(
        None, description="Reason reference(s) — replaces the full list if supplied."
    )
    supporting_information: list[AppointmentSupportingInformationInput] | None = Field(
        None, description="Supporting information — replaces the full list if supplied."
    )
    slot: list[AppointmentSlotInput] | None = Field(
        None, description="Slot(s) — replaces the full list if supplied."
    )
    based_on: list[AppointmentBasedOnInput] | None = Field(
        None, description="Based-on reference(s) — replaces the full list if supplied."
    )
    requested_period: list[AppointmentRequestedPeriodInput] | None = Field(
        None, description="Requested period(s) — replaces the full list if supplied."
    )
    participant: list[AppointmentParticipantInput] | None = Field(
        None, description="Participant(s) — replaces the full list if supplied."
    )

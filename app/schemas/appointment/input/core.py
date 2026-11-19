from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

AppointmentStatusCode = Literal[
    "proposed", "pending", "booked", "arrived", "fulfilled", "cancelled", "noshow",
    "entered-in-error", "checked-in", "waitlist",
]
ParticipantRequiredCode = Literal["required", "optional", "information-only"]
ParticipationStatusCode = Literal["accepted", "declined", "tentative", "needs-action"]

_EXAMPLE = {
    "resourceType": "Appointment",
    "status": "booked",
    "identifier": [{"system": "https://fhir-server.dev/fhir/identifier-system/appointment-id", "value": "AP-1001"}],
    "serviceCategory": [{"coding": [{"code": "17", "display": "General Practice"}]}],
    "serviceType": [{"coding": [{"code": "124", "display": "General Practice"}]}],
    "specialty": [{"coding": [{"code": "394579002", "display": "Cardiology"}]}],
    "appointmentType": {"coding": [{"code": "ROUTINE", "display": "Routine appointment"}]},
    "reasonCode": [{"text": "Annual check-up"}],
    "priority": 5,
    "description": "Discussion on the results of your recent MRI",
    "start": "2026-06-01T09:00:00Z",
    "end": "2026-06-01T09:30:00Z",
    "minutesDuration": 30,
    "slot": [{"reference": "Slot/220001"}],
    "created": "2026-05-20T10:00:00Z",
    "comment": "Further expand on the results of the MRI",
    "patientInstruction": "Please arrive 15 minutes early",
    "participant": [
        {"actor": {"reference": "Patient/10001"}, "required": "required", "status": "accepted"},
        {"actor": {"reference": "Practitioner/30001"}, "required": "required", "status": "accepted"},
    ],
    "requestedPeriod": [{"start": "2026-06-01", "end": "2026-06-07"}],
}


class AppointmentParticipantInput(FhirInputModel):
    """One Appointment.participant (R4: `status` is required, and so is at
    least one of `type` / `actor`)."""

    type: list[FhirCodeableConceptInput] | None = Field(
        None, description="Role of participant in the appointment."
    )
    actor: FhirReferenceInput | None = Field(
        None,
        description="Person, Location/HealthcareService or Device — Reference(Patient | Practitioner | PractitionerRole | RelatedPerson | Device | HealthcareService | Location). A relative reference to a Patient, Practitioner, PractitionerRole, HealthcareService or Location must exist in the caller's org (422 otherwise).",
    )
    required: ParticipantRequiredCode | None = Field(
        None, description="required | optional | information-only."
    )
    status: ParticipationStatusCode | None = Field(
        None, description="accepted | declined | tentative | needs-action (required by R4)."
    )
    period: FhirPeriodInput | None = Field(None, description="Participation period of the actor.")


class _AppointmentFields(FhirInputModel):
    """Every writable Appointment element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/appointment.html). Create and patch accept
    exactly the same fields. R4 requires `status` and at least one
    `participant`; that is enforced by base R4 validation of the stored
    document (the `java_validator` backend — the native structural check has no
    cardinality minimums), not by this model. A PATCH may omit them: it is
    merged onto the current resource before validating.

    The validated body is stored whole (AppointmentModel.content), so any valid
    R4 element is kept — including ones this model doesn't declare.
    Server-managed elements are ignored if sent: `id` (assigned from the
    appointment_id sequence) and `meta` (audit/tenant data, stamped on at read
    time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Appointment"] | None = Field(
        None, description="Optional; if supplied it must be 'Appointment'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(None, description="External Ids for this item.")
    status: AppointmentStatusCode | None = Field(
        None,
        description="proposed | pending | booked | arrived | fulfilled | cancelled | noshow | entered-in-error | checked-in | waitlist (required by R4).",
    )
    cancelationReason: FhirCodeableConceptInput | None = Field(
        None, description="The coded reason for the appointment being cancelled."
    )
    serviceCategory: list[FhirCodeableConceptInput] | None = Field(
        None, description="A broad categorization of the service that is to be performed during this appointment."
    )
    serviceType: list[FhirCodeableConceptInput] | None = Field(
        None, description="The specific service that is to be performed during this appointment."
    )
    specialty: list[FhirCodeableConceptInput] | None = Field(
        None, description="The specialty of a practitioner that would be required to perform the service requested in this appointment."
    )
    appointmentType: FhirCodeableConceptInput | None = Field(
        None, description="The style of appointment or patient that has been booked in the slot (not service type)."
    )
    reasonCode: list[FhirCodeableConceptInput] | None = Field(
        None, description="Coded reason this appointment is scheduled."
    )
    reasonReference: list[FhirReferenceInput] | None = Field(
        None, description="Reason the appointment is to take place (resource) — Reference(Condition | Procedure | Observation | ImmunizationRecommendation)."
    )
    priority: int | None = Field(
        None, ge=0, description="Used to make informed decisions if needing to re-prioritize (unsignedInt)."
    )
    description: str | None = Field(None, description="Shown on a subject line in a meeting request, or appointment list.")
    supportingInformation: list[FhirReferenceInput] | None = Field(
        None, description="Additional information to support the appointment — Reference(Any)."
    )
    start: str | None = Field(None, description="When appointment is to take place (a FHIR instant, with a timezone offset).")
    end: str | None = Field(None, description="When appointment is to conclude (a FHIR instant, with a timezone offset).")
    minutesDuration: int | None = Field(None, ge=1, description="Can be less than start/end (e.g. estimate) (positiveInt).")
    slot: list[FhirReferenceInput] | None = Field(
        None,
        description="The slots that this appointment is filling — Reference(Slot). A relative 'Slot/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    created: str | None = Field(None, description="The date that this appointment was initially created (dateTime).")
    comment: str | None = Field(None, description="Additional comments.")
    patientInstruction: str | None = Field(
        None, description="Detailed information and instructions for the patient."
    )
    basedOn: list[FhirReferenceInput] | None = Field(
        None, description="The service request this appointment is allocated to assess — Reference(ServiceRequest)."
    )
    participant: list[AppointmentParticipantInput] | None = Field(
        None, description="Participants involved in the appointment (required by R4, at least one)."
    )
    requestedPeriod: list[FhirPeriodInput] | None = Field(
        None, description="Potential date/time interval(s) requested to allocate the appointment within."
    )


class AppointmentCreateSchema(_AppointmentFields):
    """POST body — a FHIR R4 Appointment resource. Creates the appointment and
    every supplied nested element atomically in one transaction."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class AppointmentPatchSchema(_AppointmentFields):
    """PATCH body — a partial FHIR R4 Appointment (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones are
    left untouched. A supplied element replaces the stored value wholesale — a
    list (even `[]`) replaces every existing entry, an object such as
    `appointmentType` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {"example": {"status": "cancelled", "cancelationReason": {"text": "Patient unwell"}}}
    }

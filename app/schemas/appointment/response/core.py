from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRAppointmentParticipant(BaseModel):
    type: list[FHIRCodeableConcept] | None = Field(None, description="Role of participant in the appointment.")
    actor: FHIRReference | None = Field(None, description="Person, Location/HealthcareService or Device.")
    required: str | None = Field(None, description="required | optional | information-only.")
    status: str | None = Field(None, description="accepted | declined | tentative | needs-action.")
    period: FHIRPeriod | None = Field(None, description="Participation period of the actor.")


class FHIRAppointmentSchema(BaseModel):
    resourceType: str = Field("Appointment", description="Always 'Appointment'.")
    id: str = Field(..., description="Public appointment_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries."
    )
    identifier: list[FHIRIdentifier] | None = Field(None, description="External Ids for this item.")
    status: str | None = Field(
        None,
        description="proposed | pending | booked | arrived | fulfilled | cancelled | noshow | entered-in-error | checked-in | waitlist.",
    )
    cancelationReason: FHIRCodeableConcept | None = Field(None, description="The coded reason for the appointment being cancelled.")
    serviceCategory: list[FHIRCodeableConcept] | None = Field(None, description="A broad categorization of the service that is to be performed during this appointment.")
    serviceType: list[FHIRCodeableConcept] | None = Field(None, description="The specific service that is to be performed during this appointment.")
    specialty: list[FHIRCodeableConcept] | None = Field(None, description="The specialty of a practitioner that would be required to perform the service requested in this appointment.")
    appointmentType: FHIRCodeableConcept | None = Field(None, description="The style of appointment or patient that has been booked in the slot (not service type).")
    reasonCode: list[FHIRCodeableConcept] | None = Field(None, description="Coded reason this appointment is scheduled.")
    reasonReference: list[FHIRReference] | None = Field(None, description="Reason the appointment is to take place (resource).")
    priority: int | None = Field(None, description="Used to make informed decisions if needing to re-prioritize.")
    description: str | None = Field(None, description="Shown on a subject line in a meeting request, or appointment list.")
    supportingInformation: list[FHIRReference] | None = Field(None, description="Additional information to support the appointment.")
    start: str | None = Field(None, description="When appointment is to take place.")
    end: str | None = Field(None, description="When appointment is to conclude.")
    minutesDuration: int | None = Field(None, description="Can be less than start/end (e.g. estimate).")
    slot: list[FHIRReference] | None = Field(None, description="The slots that this appointment is filling.")
    created: str | None = Field(None, description="The date that this appointment was initially created.")
    comment: str | None = Field(None, description="Additional comments.")
    patientInstruction: str | None = Field(None, description="Detailed information and instructions for the patient.")
    basedOn: list[FHIRReference] | None = Field(None, description="The service request this appointment is allocated to assess.")
    participant: list[FHIRAppointmentParticipant] | None = Field(None, description="Participants involved in the appointment.")
    requestedPeriod: list[FHIRPeriod] | None = Field(None, description="Potential date/time interval(s) requested to allocate the appointment within.")


class FHIRAppointmentBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRAppointmentSchema | dict = Field(
        ...,
        description="An Appointment (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Practitioner / PractitionerRole / HealthcareService / Location / Slot (from _include), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRAppointmentBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRAppointmentBundleEntry] | None = None

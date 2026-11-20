from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRAppointmentResponseSchema(BaseModel):
    resourceType: str = Field("AppointmentResponse", description="Always 'AppointmentResponse'.")
    id: str = Field(..., description="Public appointment_response_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries."
    )
    identifier: list[FHIRIdentifier] | None = Field(None, description="External Ids for this item.")
    appointment: FHIRReference | None = Field(None, description="Appointment this response is replying to.")
    start: str | None = Field(None, description="Time from appointment, or requested new start time.")
    end: str | None = Field(None, description="Time from appointment, or requested new end time.")
    participantType: list[FHIRCodeableConcept] | None = Field(None, description="Role of participant in the appointment.")
    actor: FHIRReference | None = Field(None, description="Person, Location, HealthcareService, or Device.")
    participantStatus: str | None = Field(None, description="accepted | declined | tentative | needs-action.")
    comment: str | None = Field(None, description="Additional comments.")


class FHIRAppointmentResponseBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRAppointmentResponseSchema | dict = Field(
        ...,
        description="An AppointmentResponse (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Appointment / Patient / Practitioner / PractitionerRole / HealthcareService / Location (from _include), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRAppointmentResponseBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRAppointmentResponseBundleEntry] | None = None

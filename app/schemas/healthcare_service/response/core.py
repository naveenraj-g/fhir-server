from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRAttachment,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink

from .backbone import (
    FHIRHealthcareServiceAvailableTime,
    FHIRHealthcareServiceEligibility,
    FHIRHealthcareServiceNotAvailable,
)


class FHIRHealthcareServiceSchema(BaseModel):
    resourceType: str = Field(
        "HealthcareService", description="Always 'HealthcareService'."
    )
    id: str = Field(..., description="Public healthcare_service_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External identifiers for this item."
    )
    active: bool | None = Field(
        None, description="Whether this HealthcareService record is in active use."
    )
    providedBy: FHIRReference | None = Field(
        None, description="Organization that provides this service."
    )
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="Broad category of service being performed or delivered."
    )
    type: list[FHIRCodeableConcept] | None = Field(
        None, description="Type of service that may be delivered or performed."
    )
    specialty: list[FHIRCodeableConcept] | None = Field(
        None, description="Specialties handled by the HealthcareService."
    )
    location: list[FHIRReference] | None = Field(
        None, description="Location(s) where service may be provided."
    )
    name: str | None = Field(
        None,
        description="Description of service as presented to a consumer while searching.",
    )
    comment: str | None = Field(
        None,
        description="Additional description and/or any specific issues not covered elsewhere.",
    )
    extraDetails: str | None = Field(
        None, description="Extra details about the service (markdown)."
    )
    photo: FHIRAttachment | None = Field(
        None, description="Facilitates quick identification of the service."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None, description="Contacts related to the healthcare service."
    )
    coverageArea: list[FHIRReference] | None = Field(
        None, description="Location(s) service is intended for/available to."
    )
    serviceProvisionCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Conditions under which service is available/offered."
    )
    eligibility: list[FHIRHealthcareServiceEligibility] | None = Field(
        None,
        description="Specific eligibility requirements required to use the service.",
    )
    program: list[FHIRCodeableConcept] | None = Field(
        None, description="Programs that this service is applicable to."
    )
    characteristic: list[FHIRCodeableConcept] | None = Field(
        None, description="Collection of characteristics (attributes)."
    )
    communication: list[FHIRCodeableConcept] | None = Field(
        None, description="The language that this service is offered in."
    )
    referralMethod: list[FHIRCodeableConcept] | None = Field(
        None, description="Ways that the service accepts referrals."
    )
    appointmentRequired: bool | None = Field(
        None, description="If an appointment is required for access to this service."
    )
    availableTime: list[FHIRHealthcareServiceAvailableTime] | None = Field(
        None, description="Times the Service Site is available."
    )
    notAvailable: list[FHIRHealthcareServiceNotAvailable] | None = Field(
        None, description="Not available during this time due to provided reason."
    )
    availabilityExceptions: str | None = Field(
        None, description="Description of availability exceptions."
    )
    endpoint: list[FHIRReference] | None = Field(
        None,
        description="Technical endpoints providing access to electronic services operated for the healthcare service.",
    )


class FHIRHealthcareServiceBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRHealthcareServiceSchema | dict = Field(
        ...,
        description="A HealthcareService (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource of another type (an Organization or Location from _include), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRHealthcareServiceBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRHealthcareServiceBundleEntry] | None = None

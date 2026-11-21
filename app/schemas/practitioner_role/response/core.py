from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink

from .backbone import (
    FHIRPractitionerRoleAvailableTime,
    FHIRPractitionerRoleNotAvailable,
)


class FHIRPractitionerRoleSchema(BaseModel):
    resourceType: str = Field(
        "PractitionerRole", description="Always 'PractitionerRole'."
    )
    id: str = Field(..., description="Public practitioner_role_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Business Identifiers that are specific to a role/location."
    )
    active: bool | None = Field(
        None, description="Whether this practitioner role record is in active use."
    )
    period: FHIRPeriod | None = Field(
        None,
        description="The period during which the practitioner is authorized to perform in these role(s).",
    )
    practitioner: FHIRReference | None = Field(
        None,
        description="Practitioner that is able to provide the defined services for the organization.",
    )
    organization: FHIRReference | None = Field(
        None, description="Organization where the roles are available."
    )
    code: list[FHIRCodeableConcept] | None = Field(
        None, description="Roles which this practitioner may perform."
    )
    specialty: list[FHIRCodeableConcept] | None = Field(
        None, description="Specific specialty of the practitioner."
    )
    location: list[FHIRReference] | None = Field(
        None, description="The location(s) at which this practitioner provides care."
    )
    healthcareService: list[FHIRReference] | None = Field(
        None,
        description="The list of healthcare services that this worker provides for this role's Organization/Location(s).",
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None,
        description="Contact details that are specific to the role/location/service.",
    )
    availableTime: list[FHIRPractitionerRoleAvailableTime] | None = Field(
        None, description="Times the Service Site is available."
    )
    notAvailable: list[FHIRPractitionerRoleNotAvailable] | None = Field(
        None, description="Not available during this time due to provided reason."
    )
    availabilityExceptions: str | None = Field(
        None, description="Description of availability exceptions."
    )
    endpoint: list[FHIRReference] | None = Field(
        None,
        description="Technical endpoints providing access to services operated for the practitioner with this role.",
    )


class FHIRPractitionerRoleBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRPractitionerRoleSchema | dict = Field(
        ...,
        description="A PractitionerRole (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource of another type (a Practitioner, Organization, Location, HealthcareService or Endpoint from _include), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRPractitionerRoleBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRPractitionerRoleBundleEntry] | None = None

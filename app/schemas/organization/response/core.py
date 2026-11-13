from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRAddress,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)

from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink

from .contact import FHIROrganizationContact

class FHIROrganizationSchema(BaseModel):
    resourceType: str = Field("Organization", description="Always 'Organization'.")
    id: str = Field(..., description="Public organization_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries. Not yet validated against registered extension definitions.",
    )
    active: bool | None = Field(
        None, description="Whether the organization's record is still in active use."
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None,
        description="Identifier(s) for the organization that is used to identify the organization across multiple disparate systems.",
    )
    type: list[FHIRCodeableConcept] | None = Field(
        None, description="The kind(s) of organization that this is."
    )
    name: str | None = Field(
        None, description="A name associated with the organization."
    )
    alias: list[str] | None = Field(
        None,
        description="A list of alternate names that the organization is known as, or was known as in the past.",
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None, description="A contact detail for the organization."
    )
    address: list[FHIRAddress] | None = Field(
        None, description="An address for the organization."
    )
    partOf: FHIRReference | None = Field(
        None, description="The organization of which this organization forms a part."
    )
    contact: list[FHIROrganizationContact] | None = Field(
        None, description="Contact for the organization for a certain purpose."
    )
    endpoint: list[FHIRReference] | None = Field(
        None,
        description="Technical endpoints providing access to services operated for the organization.",
    )


class FHIROrganizationBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIROrganizationSchema | dict = Field(
        ...,
        description="An Organization (match/include; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource of another type (e.g. a Location from _revinclude=Location:organization), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIROrganizationBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIROrganizationBundleEntry] | None = None

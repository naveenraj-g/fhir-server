from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRCoding,
    FHIRContactPoint,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIREndpointSchema(BaseModel):
    resourceType: str = Field("Endpoint", description="Always 'Endpoint'.")
    id: str = Field(..., description="Public endpoint_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries."
    )
    identifier: list[FHIRIdentifier] | None = Field(None, description="Identifies this endpoint across multiple systems.")
    status: str | None = Field(None, description="active | suspended | error | off | entered-in-error | test.")
    connectionType: FHIRCoding | None = Field(None, description="Protocol/Profile/Standard to be used with this endpoint connection.")
    name: str | None = Field(None, description="A name that this endpoint can be identified by.")
    managingOrganization: FHIRReference | None = Field(None, description="Organization that manages this endpoint.")
    contact: list[FHIRContactPoint] | None = Field(None, description="Contact details for source (e.g. troubleshooting).")
    period: FHIRPeriod | None = Field(None, description="Interval the endpoint is expected to be operational.")
    payloadType: list[FHIRCodeableConcept] | None = Field(None, description="The type of content that may be used at this endpoint.")
    payloadMimeType: list[str] | None = Field(None, description="Mimetype to send.")
    address: str | None = Field(None, description="The technical base address for connecting to this endpoint.")
    header: list[str] | None = Field(None, description="Usage depends on the channel type (e.g. HTTP headers).")


class FHIREndpointBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIREndpointSchema | dict = Field(
        ...,
        description="An Endpoint (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource of another type (an Organization, Location or HealthcareService from _include / _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIREndpointBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIREndpointBundleEntry] | None = None

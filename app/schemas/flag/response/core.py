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


class FHIRFlagSchema(BaseModel):
    resourceType: str = Field("Flag", description="Always 'Flag'.")
    id: str = Field(..., description="Public flag_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Business identifier."
    )
    status: str | None = Field(
        None, description="active | inactive | entered-in-error."
    )
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="Clinical, administrative, etc."
    )
    code: FHIRCodeableConcept | None = Field(
        None, description="Coded or textual message to display to user."
    )
    subject: FHIRReference | None = Field(None, description="Who/What is flag about.")
    period: FHIRPeriod | None = Field(
        None, description="Time period when flag is active."
    )
    encounter: FHIRReference | None = Field(
        None, description="Alert relevant during encounter."
    )
    author: FHIRReference | None = Field(None, description="Flag creator.")


class FHIRFlagBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRFlagSchema | dict = Field(
        ...,
        description="A Flag (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRFlagBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRFlagBundleEntry] | None = None

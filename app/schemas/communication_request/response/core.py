"""Response schemas for CommunicationRequest (generated; see scripts/generate_fhir_resources.py)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.datatypes import FHIRBundle, FHIRMeta
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink
from app.schemas.fhir_resources.communication_request import CommunicationRequest


class FHIRCommunicationRequestSchema(CommunicationRequest):
    "A FHIR R4 CommunicationRequest as served: the stored document with `id` and `meta` stamped on."

    resourceType: str = Field(
        "CommunicationRequest", description="Always 'CommunicationRequest'."
    )
    id: str = Field(..., description="Public communication_request_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only.",
    )


class FHIRCommunicationRequestBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRCommunicationRequestSchema | dict = Field(
        ...,
        description="A CommunicationRequest (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRCommunicationRequestBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRCommunicationRequestBundleEntry] | None = None

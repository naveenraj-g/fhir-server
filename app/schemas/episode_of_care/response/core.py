"""Response schemas for EpisodeOfCare (generated; see scripts/generate_fhir_resources.py)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import FHIRBundle
from app.schemas.common.searchset import FHIRBundleEntrySearch, FHIRBundleLink
from app.schemas.fhir_datatypes import Meta
from app.schemas.fhir_resources.episode_of_care import EpisodeOfCare


class FHIREpisodeOfCareSchema(EpisodeOfCare):
    "A FHIR R4 EpisodeOfCare as served: the stored document with `id` and `meta` stamped on."

    resourceType: str = Field("EpisodeOfCare", description="Always 'EpisodeOfCare'.")
    id: str = Field(..., description="Public episode_of_care_id as a string.")
    meta: Meta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only.",
    )


class FHIREpisodeOfCareBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIREpisodeOfCareSchema | dict = Field(
        ...,
        description="A EpisodeOfCare (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIREpisodeOfCareBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIREpisodeOfCareBundleEntry] | None = None

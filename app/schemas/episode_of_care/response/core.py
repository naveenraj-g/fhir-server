"""Response schemas for EpisodeOfCare (generated; see scripts/generate_fhir_resources.py)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import FHIRBundle
from app.schemas.common.examples import bundle_example, served_example
from app.schemas.common.searchset import FHIRBundleEntrySearch, FHIRBundleLink
from app.schemas.episode_of_care.input.core import _CREATE_EXAMPLE
from app.schemas.fhir_datatypes import Meta
from app.schemas.fhir_resources.episode_of_care import EpisodeOfCare

_EXAMPLE = served_example("EpisodeOfCare", "350000", _CREATE_EXAMPLE)


class FHIREpisodeOfCareSchema(EpisodeOfCare):
    "A FHIR R4 EpisodeOfCare as served: the stored document with `id` and `meta` stamped on."

    model_config = ConfigDict(json_schema_extra={"example": _EXAMPLE})

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
    model_config = ConfigDict(
        json_schema_extra={"example": bundle_example("/episodes-of-care", _EXAMPLE)}
    )

    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIREpisodeOfCareBundleEntry] | None = None

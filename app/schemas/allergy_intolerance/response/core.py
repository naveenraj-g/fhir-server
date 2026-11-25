"""Response schemas for AllergyIntolerance (generated; see scripts/generate_fhir_resources.py)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.datatypes import FHIRBundle, FHIRMeta
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink
from app.schemas.fhir_resources.allergy_intolerance import AllergyIntolerance


class FHIRAllergyIntoleranceSchema(AllergyIntolerance):
    "A FHIR R4 AllergyIntolerance as served: the stored document with `id` and `meta` stamped on."

    resourceType: str = Field(
        "AllergyIntolerance", description="Always 'AllergyIntolerance'."
    )
    id: str = Field(..., description="Public allergy_intolerance_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only.",
    )


class FHIRAllergyIntoleranceBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRAllergyIntoleranceSchema | dict = Field(
        ...,
        description="A AllergyIntolerance (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRAllergyIntoleranceBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRAllergyIntoleranceBundleEntry] | None = None

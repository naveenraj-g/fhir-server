"""Response schemas for FamilyMemberHistory (generated; see scripts/generate_fhir_resources.py)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.common import FHIRBundle
from app.schemas.common.searchset import FHIRBundleEntrySearch, FHIRBundleLink
from app.schemas.fhir_datatypes import Meta
from app.schemas.fhir_resources.family_member_history import FamilyMemberHistory


class FHIRFamilyMemberHistorySchema(FamilyMemberHistory):
    "A FHIR R4 FamilyMemberHistory as served: the stored document with `id` and `meta` stamped on."

    resourceType: str = Field(
        "FamilyMemberHistory", description="Always 'FamilyMemberHistory'."
    )
    id: str = Field(..., description="Public family_member_history_id as a string.")
    meta: Meta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only.",
    )


class FHIRFamilyMemberHistoryBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRFamilyMemberHistorySchema | dict = Field(
        ...,
        description="A FamilyMemberHistory (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRFamilyMemberHistoryBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRFamilyMemberHistoryBundleEntry] | None = None

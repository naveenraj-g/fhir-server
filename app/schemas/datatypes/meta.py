from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.datatypes.coding import FHIRCoding


class FHIRMeta(BaseModel):
    """FHIR R4 Meta — infrastructure-maintained metadata about a resource.
    `lastUpdated` is the only field this server populates natively today
    (from the row's `updated_at`); `security`/`tag` reuse FHIRCoding since
    both are 0..* Coding per spec. `extension` is where resource metadata
    with no native Meta field rides — e.g. Organization's `org_id`/
    `created_by`/`updated_by`/`created_at` (see
    app.fhir.mappers.organization.fhir._fhir_meta) — same raw,
    not-yet-registered-extension-definition convention as a resource's own
    top-level `extension` field."""

    versionId: Optional[str] = Field(None, description="Version-specific identifier.")
    lastUpdated: Optional[str] = Field(
        None, description="ISO 8601 instant the resource version last changed."
    )
    source: Optional[str] = Field(
        None, description="URI identifying where this resource currently resides or was generated."
    )
    profile: Optional[List[str]] = Field(
        None, description="Canonical URLs of profiles this resource claims to conform to."
    )
    security: Optional[List[FHIRCoding]] = Field(
        None, description="Security labels applied to this resource."
    )
    tag: Optional[List[FHIRCoding]] = Field(
        None, description="Tags applied to this resource for workflow/categorization."
    )
    extension: Optional[List[dict]] = Field(
        None,
        description="Meta-level FHIR extensions, as raw [{url, valueType, value}, ...] entries. Not yet validated against registered extension definitions.",
    )

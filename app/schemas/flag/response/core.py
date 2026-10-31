from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    AuditFields,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
    PlainCodingRow,
)

from .category import PlainFlagCategory
from .identifier import PlainFlagIdentifier

# ── FHIR (camelCase) ──────────────────────────────────────────────────────────


class FHIRFlagSchema(BaseModel):
    resourceType: str = Field("Flag", description="Always 'Flag'.")
    id: str = Field(..., description="Public flag_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus org_id/created_by/updated_by/created_at as extensions.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Business identifier for each flag."
    )
    status: str = Field(
        ..., description="active | inactive | entered-in-error."
    )
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="Clinical, administrative, etc."
    )
    code: FHIRCodeableConcept = Field(
        ..., description="Coded aspect of flag."
    )
    subject: FHIRReference = Field(
        ..., description="Who/What is the flag about."
    )
    period: FHIRPeriod | None = Field(
        None, description="Time period when flag is active."
    )
    encounter: FHIRReference | None = Field(
        None, description="Alert relevant to this encounter."
    )
    author: FHIRReference | None = Field(
        None, description="Flag creator."
    )


class FHIRFlagBundleEntry(BaseModel):
    resource: FHIRFlagSchema


class FHIRFlagBundle(FHIRBundle):
    entry: list[FHIRFlagBundleEntry] | None = None


# ── Plain (snake_case) ─────────────────────────────────────────────────────────


class PlainFlagResponse(AuditFields):
    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Public flag_id.")
    status: str = Field(..., description="active | inactive | entered-in-error.")
    code_text: str | None = Field(None, description="Text representation of flag code.")
    code_codings: list[PlainCodingRow] | None = Field(
        None, description="Codings for flag code."
    )
    subject_reference: str = Field(
        ..., description="Raw literal string of subject reference."
    )
    subject_type: str | None = Field(
        None, description="Target resource type of subject."
    )
    subject_id: int | None = Field(
        None, description="Resolved public subject ID."
    )
    subject_display: str | None = Field(
        None, description="Display text for subject reference."
    )
    period_start: str | None = Field(
        None, description="Start of validity period."
    )
    period_end: str | None = Field(
        None, description="End of validity period."
    )
    encounter_reference: str | None = Field(
        None, description="Literal encounter reference string."
    )
    encounter_type: str | None = Field(
        None, description="Target type of encounter reference."
    )
    encounter_id: int | None = Field(
        None, description="Resolved public encounter ID."
    )
    encounter_display: str | None = Field(
        None, description="Display text for encounter reference."
    )
    author_reference: str | None = Field(
        None, description="Literal author reference string."
    )
    author_type: str | None = Field(
        None, description="Target type of author reference."
    )
    author_id: int | None = Field(
        None, description="Resolved public author ID."
    )
    author_display: str | None = Field(
        None, description="Display text for author reference."
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions."
    )
    identifiers: list[PlainFlagIdentifier] | None = Field(
        None, description="Identifiers for this flag."
    )
    categories: list[PlainFlagCategory] | None = Field(
        None, description="Categories for this flag."
    )


class PaginatedFlagResponse(BaseModel):
    total: int = Field(..., description="Total matching records.")
    limit: int = Field(..., description="Maximum results returned.")
    offset: int = Field(..., description="Offset applied.")
    data: list[PlainFlagResponse] = Field(
        ..., description="Page of flag records."
    )

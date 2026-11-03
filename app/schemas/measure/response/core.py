import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.measure.response.codeable_concept import (
    PlainMeasureConcept,
    PlainMeasureSingleConcept,
)
from app.schemas.measure.response.contact import (
    FHIRMeasureContact,
    PlainMeasureContact,
)
from app.schemas.measure.response.group import (
    FHIRMeasureGroup,
    PlainMeasureGroup,
)
from app.schemas.measure.response.identifier import PlainMeasureIdentifier
from app.schemas.measure.response.related_artifact import (
    FHIRMeasureRelatedArtifact,
    PlainMeasureRelatedArtifact,
)
from app.schemas.measure.response.supplemental_data import (
    FHIRMeasureSupplementalData,
    PlainMeasureSupplementalData,
)
from app.schemas.measure.response.use_context import (
    FHIRMeasureUseContext,
    PlainMeasureUseContext,
)


class FHIRMeasureSchema(BaseModel):
    """FHIR R4 Measure resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Measure"] = "Measure"
    id: str | None = None
    meta: FHIRMeta | None = None
    extension: list[dict[str, Any]] | None = None
    url: str | None = None
    identifier: list[FHIRIdentifier] | None = None
    version: str | None = None
    name: str | None = None
    title: str | None = None
    subtitle: str | None = None
    status: str = Field(..., description="draft | active | retired | unknown.")
    experimental: bool | None = None

    subjectCodeableConcept: FHIRCodeableConcept | None = None
    subjectReference: FHIRReference | None = None

    date: dt.datetime | None = None
    publisher: str | None = None
    contact: list[FHIRMeasureContact] | None = None
    description: str | None = None
    useContext: list[FHIRMeasureUseContext] | None = None
    jurisdiction: list[FHIRCodeableConcept] | None = None
    purpose: str | None = None
    usage: str | None = None
    copyright: str | None = None
    approvalDate: dt.date | None = None
    lastReviewDate: dt.date | None = None
    effectivePeriod: FHIRPeriod | None = None
    topic: list[FHIRCodeableConcept] | None = None
    author: list[FHIRMeasureContact] | None = None
    editor: list[FHIRMeasureContact] | None = None
    reviewer: list[FHIRMeasureContact] | None = None
    endorser: list[FHIRMeasureContact] | None = None
    relatedArtifact: list[FHIRMeasureRelatedArtifact] | None = None
    library: list[str] | None = None
    disclaimer: str | None = None
    scoring: FHIRCodeableConcept | None = None
    compositeScoring: FHIRCodeableConcept | None = None
    type: list[FHIRCodeableConcept] | None = None
    riskAdjustment: str | None = None
    rateAggregation: str | None = None
    rationale: str | None = None
    clinicalRecommendationStatement: str | None = None
    improvementNotation: FHIRCodeableConcept | None = None
    definition: list[str] | None = None
    guidance: str | None = None
    group: list[FHIRMeasureGroup] | None = None
    supplementalData: list[FHIRMeasureSupplementalData] | None = None


class PlainMeasureResponse(BaseModel):
    """Plain JSON representation of Measure."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Public sequence measure_id.")
    url: str | None = None
    identifier: list[PlainMeasureIdentifier] | None = None
    version: str | None = None
    name: str | None = None
    title: str | None = None
    subtitle: str | None = None
    status: str = Field(..., description="draft | active | retired | unknown.")
    experimental: bool | None = None

    subject_codeable_concept: PlainMeasureSingleConcept | None = None
    subject_reference: str | None = None
    subject_display: str | None = None

    date: dt.datetime | None = None
    publisher: str | None = None
    contact: list[PlainMeasureContact] | None = None
    description: str | None = None
    use_context: list[PlainMeasureUseContext] | None = None
    jurisdiction: list[PlainMeasureConcept] | None = None
    purpose: str | None = None
    usage: str | None = None
    copyright: str | None = None
    approval_date: dt.date | None = None
    last_review_date: dt.date | None = None
    effective_period_start: dt.datetime | None = None
    effective_period_end: dt.datetime | None = None
    topic: list[PlainMeasureConcept] | None = None
    author: list[PlainMeasureContact] | None = None
    editor: list[PlainMeasureContact] | None = None
    reviewer: list[PlainMeasureContact] | None = None
    endorser: list[PlainMeasureContact] | None = None
    related_artifact: list[PlainMeasureRelatedArtifact] | None = None
    library: list[str] | None = None
    disclaimer: str | None = None
    scoring: PlainMeasureSingleConcept | None = None
    composite_scoring: PlainMeasureSingleConcept | None = None
    type: list[PlainMeasureConcept] | None = None
    risk_adjustment: str | None = None
    rate_aggregation: str | None = None
    rationale: str | None = None
    clinical_recommendation_statement: str | None = None
    improvement_notation: PlainMeasureSingleConcept | None = None
    definition: list[str] | None = None
    guidance: str | None = None
    group: list[PlainMeasureGroup] | None = None
    supplemental_data: list[PlainMeasureSupplementalData] | None = None

    extension: list[dict[str, Any]] | None = None
    created_by: str = Field(..., description="Creator user ID.")
    updated_by: str | None = Field(None, description="Last updater user ID.")
    created_at: dt.datetime = Field(..., description="Creation timestamp.")
    updated_at: dt.datetime = Field(..., description="Last update timestamp.")


class PaginatedMeasureResponse(BaseModel):
    """Paginated plain Measure list response."""

    model_config = ConfigDict(extra="allow")

    data: list[PlainMeasureResponse] = Field(..., description="List of measures.")
    total: int | None = Field(None, description="Total matching records.")
    limit: int = Field(..., description="Page size.")
    offset: int = Field(..., description="Page offset.")


class FHIRMeasureBundleEntry(BaseModel):
    """Single entry in a Measure FHIR Bundle."""

    model_config = ConfigDict(extra="allow")

    fullUrl: str | None = Field(None, description="Full URL for resource.")
    resource: FHIRMeasureSchema = Field(..., description="Measure resource.")


class FHIRMeasureBundle(BaseModel):
    """FHIR R4 Bundle for Measure resources."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Bundle"] = "Bundle"
    type: str = Field("searchset", description="Bundle type.")
    total: int | None = Field(None, description="Total matching records.")
    entry: list[FHIRMeasureBundleEntry] = Field(
        default_factory=list, description="Bundle entries."
    )

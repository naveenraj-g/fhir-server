import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.activity_definition.response.contact import (
    FHIRActivityDefinitionContact,
    PlainActivityDefinitionContact,
)
from app.schemas.activity_definition.response.dosage import (
    FHIRActivityDefinitionDosage,
    PlainActivityDefinitionDosage,
)
from app.schemas.activity_definition.response.dynamic_value import (
    FHIRActivityDefinitionDynamicValue,
    PlainActivityDefinitionDynamicValue,
)
from app.schemas.activity_definition.response.identifier import (
    PlainActivityDefinitionIdentifier,
)
from app.schemas.activity_definition.response.participant import (
    FHIRActivityDefinitionParticipant,
    PlainActivityDefinitionParticipant,
)
from app.schemas.activity_definition.response.related_artifact import (
    FHIRActivityDefinitionRelatedArtifact,
    PlainActivityDefinitionRelatedArtifact,
)
from app.schemas.activity_definition.response.use_context import (
    FHIRActivityDefinitionUseContext,
    PlainActivityDefinitionUseContext,
)
from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRQuantity,
    FHIRRange,
    FHIRReference,
    PlainCodingRow,
)


class PlainActivityDefinitionConcept(BaseModel):
    """Plain representation of a 0..* CodeableConcept child entry."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    text: str | None = None
    codings: list[PlainCodingRow] | None = None


class PlainActivityDefinitionSingleConcept(BaseModel):
    """Plain representation of a 0..1 CodeableConcept."""

    model_config = ConfigDict(extra="allow")

    text: str | None = None
    codings: list[PlainCodingRow] | None = None


class PlainActivityDefinitionRequirement(BaseModel):
    """Plain representation of a Requirement Reference entry."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    reference: str | None = None
    display: str | None = None


class FHIRActivityDefinitionSchema(BaseModel):
    """FHIR R4 ActivityDefinition resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["ActivityDefinition"] = "ActivityDefinition"
    id: str | None = None
    meta: FHIRMeta | None = None
    url: str | None = None
    identifier: list[FHIRIdentifier] | None = None
    version: str | None = None
    name: str | None = None
    title: str | None = None
    subtitle: str | None = None
    status: str = Field(..., description="draft | active | retired | unknown.")
    experimental: bool | None = None
    date: dt.datetime | None = None
    publisher: str | None = None
    contact: list[FHIRActivityDefinitionContact] | None = None
    description: str | None = None
    useContext: list[FHIRActivityDefinitionUseContext] | None = None
    jurisdiction: list[FHIRCodeableConcept] | None = None
    purpose: str | None = None
    usage: str | None = None
    copyright: str | None = None
    approvalDate: dt.date | None = None
    lastReviewDate: dt.date | None = None
    effectivePeriod: FHIRPeriod | None = None
    topic: list[FHIRCodeableConcept] | None = None
    author: list[FHIRActivityDefinitionContact] | None = None
    editor: list[FHIRActivityDefinitionContact] | None = None
    reviewer: list[FHIRActivityDefinitionContact] | None = None
    endorser: list[FHIRActivityDefinitionContact] | None = None
    relatedArtifact: list[FHIRActivityDefinitionRelatedArtifact] | None = None
    library: list[str] | None = None
    kind: str | None = None
    profile: str | None = None
    code: FHIRCodeableConcept | None = None
    intent: str | None = None
    priority: str | None = None
    doNotPerform: bool | None = None

    timingTiming: dict | None = None
    timingDateTime: dt.datetime | None = None
    timingAge: FHIRQuantity | None = None
    timingPeriod: FHIRPeriod | None = None
    timingRange: FHIRRange | None = None
    timingDuration: FHIRQuantity | None = None

    location: FHIRReference | None = None
    participant: list[FHIRActivityDefinitionParticipant] | None = None
    productCodeableConcept: FHIRCodeableConcept | None = None
    productReference: FHIRReference | None = None
    quantity: FHIRQuantity | None = None
    dosage: list[FHIRActivityDefinitionDosage] | None = None
    bodySite: list[FHIRCodeableConcept] | None = None
    specimenRequirement: list[FHIRReference] | None = None
    observationRequirement: list[FHIRReference] | None = None
    observationResultRequirement: list[FHIRReference] | None = None
    transform: str | None = None
    dynamicValue: list[FHIRActivityDefinitionDynamicValue] | None = None
    subjectCodeableConcept: FHIRCodeableConcept | None = None
    subjectReference: FHIRReference | None = None

    extension: list[dict] | None = None


class PlainActivityDefinitionResponse(BaseModel):
    """Plain (snake_case) ActivityDefinition response schema."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Public sequence ID.")
    tenant_id: str = Field(..., description="Owning tenant/organization ID.")
    url: str | None = None
    identifier: list[PlainActivityDefinitionIdentifier] | None = None
    version: str | None = None
    name: str | None = None
    title: str | None = None
    subtitle: str | None = None
    status: str
    experimental: bool | None = None
    date: dt.datetime | None = None
    publisher: str | None = None
    contact: list[PlainActivityDefinitionContact] | None = None
    description: str | None = None
    use_context: list[PlainActivityDefinitionUseContext] | None = None
    jurisdiction: list[PlainActivityDefinitionConcept] | None = None
    purpose: str | None = None
    usage: str | None = None
    copyright: str | None = None
    approval_date: dt.date | None = None
    last_review_date: dt.date | None = None
    effective_period_start: dt.datetime | None = None
    effective_period_end: dt.datetime | None = None
    topic: list[PlainActivityDefinitionConcept] | None = None
    author: list[PlainActivityDefinitionContact] | None = None
    editor: list[PlainActivityDefinitionContact] | None = None
    reviewer: list[PlainActivityDefinitionContact] | None = None
    endorser: list[PlainActivityDefinitionContact] | None = None
    related_artifact: list[PlainActivityDefinitionRelatedArtifact] | None = None
    library: list[str] | None = None
    kind: str | None = None
    profile: str | None = None
    code: PlainActivityDefinitionSingleConcept | None = None
    intent: str | None = None
    priority: str | None = None
    do_not_perform: bool | None = None

    timing_timing: dict | None = None
    timing_date_time: dt.datetime | None = None
    timing_age_value: float | None = None
    timing_age_unit: str | None = None
    timing_age_system: str | None = None
    timing_age_code: str | None = None
    timing_period_start: dt.datetime | None = None
    timing_period_end: dt.datetime | None = None
    timing_range_low_value: float | None = None
    timing_range_low_unit: str | None = None
    timing_range_high_value: float | None = None
    timing_range_high_unit: str | None = None
    timing_duration_value: float | None = None
    timing_duration_unit: str | None = None
    timing_duration_system: str | None = None
    timing_duration_code: str | None = None

    location: str | None = None
    location_display: str | None = None
    participant: list[PlainActivityDefinitionParticipant] | None = None
    product_codeable_concept: PlainActivityDefinitionSingleConcept | None = None
    product_reference: str | None = None
    product_display: str | None = None
    quantity_value: float | None = None
    quantity_comparator: str | None = None
    quantity_unit: str | None = None
    quantity_system: str | None = None
    quantity_code: str | None = None
    dosage: list[PlainActivityDefinitionDosage] | None = None
    body_site: list[PlainActivityDefinitionConcept] | None = None
    specimen_requirement: list[PlainActivityDefinitionRequirement] | None = None
    observation_requirement: list[PlainActivityDefinitionRequirement] | None = None
    observation_result_requirement: list[PlainActivityDefinitionRequirement] | None = None
    transform: str | None = None
    dynamic_value: list[PlainActivityDefinitionDynamicValue] | None = None

    subject_codeable_concept: PlainActivityDefinitionSingleConcept | None = None
    subject_reference: str | None = None
    subject_display: str | None = None

    extension: list[dict] | None = None
    created_by: str = Field(..., description="Creator user ID.")
    updated_by: str | None = Field(None, description="Last updater user ID.")
    created_at: dt.datetime = Field(..., description="Creation timestamp.")
    updated_at: dt.datetime = Field(..., description="Last update timestamp.")


class PaginatedActivityDefinitionResponse(BaseModel):
    """Paginated plain ActivityDefinition list response."""

    model_config = ConfigDict(extra="allow")

    data: list[PlainActivityDefinitionResponse] = Field(..., description="List of activity definitions.")
    total: int | None = Field(None, description="Total matching records.")
    limit: int = Field(..., description="Page size.")
    offset: int = Field(..., description="Page offset.")


class FHIRActivityDefinitionBundleEntry(BaseModel):
    """Single entry in an ActivityDefinition FHIR Bundle."""

    model_config = ConfigDict(extra="allow")

    fullUrl: str | None = Field(None, description="Full URL for resource.")
    resource: FHIRActivityDefinitionSchema = Field(..., description="ActivityDefinition resource.")


class FHIRActivityDefinitionBundle(BaseModel):
    """FHIR R4 Bundle for ActivityDefinition resources."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Bundle"] = "Bundle"
    type: str = Field("searchset", description="Bundle type.")
    total: int | None = Field(None, description="Total matching records.")
    entry: list[FHIRActivityDefinitionBundleEntry] = Field(
        default_factory=list, description="Bundle entries."
    )

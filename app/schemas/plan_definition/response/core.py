import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
    PlainCodingRow,
)
from app.schemas.plan_definition.response.action import (
    FHIRPlanDefinitionAction,
    PlainPlanDefinitionAction,
)
from app.schemas.plan_definition.response.contact import (
    FHIRPlanDefinitionContact,
    PlainPlanDefinitionContact,
)
from app.schemas.plan_definition.response.goal import (
    FHIRPlanDefinitionGoal,
    PlainPlanDefinitionGoal,
)
from app.schemas.plan_definition.response.identifier import (
    PlainPlanDefinitionIdentifier,
)
from app.schemas.plan_definition.response.related_artifact import (
    FHIRPlanDefinitionRelatedArtifact,
    PlainPlanDefinitionRelatedArtifact,
)
from app.schemas.plan_definition.response.use_context import (
    FHIRPlanDefinitionUseContext,
    PlainPlanDefinitionUseContext,
)


class PlainPlanDefinitionConcept(BaseModel):
    """Plain representation of a 0..* CodeableConcept child entry."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    text: str | None = None
    codings: list[PlainCodingRow] | None = None


class PlainPlanDefinitionSingleConcept(BaseModel):
    """Plain representation of a 0..1 CodeableConcept."""

    model_config = ConfigDict(extra="allow")

    text: str | None = None
    codings: list[PlainCodingRow] | None = None


class FHIRPlanDefinitionSchema(BaseModel):
    """FHIR R4 PlanDefinition resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["PlanDefinition"] = "PlanDefinition"
    id: str | None = None
    meta: FHIRMeta | None = None
    url: str | None = None
    identifier: list[FHIRIdentifier] | None = None
    version: str | None = None
    name: str | None = None
    title: str | None = None
    subtitle: str | None = None
    type: FHIRCodeableConcept | None = None
    status: str = Field(..., description="draft | active | retired | unknown.")
    experimental: bool | None = None
    subjectCodeableConcept: FHIRCodeableConcept | None = None
    subjectReference: FHIRReference | None = None
    date: dt.datetime | None = None
    publisher: str | None = None
    contact: list[FHIRPlanDefinitionContact] | None = None
    description: str | None = None
    useContext: list[FHIRPlanDefinitionUseContext] | None = None
    jurisdiction: list[FHIRCodeableConcept] | None = None
    purpose: str | None = None
    usage: str | None = None
    copyright: str | None = None
    approvalDate: dt.date | None = None
    lastReviewDate: dt.date | None = None
    effectivePeriod: FHIRPeriod | None = None
    topic: list[FHIRCodeableConcept] | None = None
    author: list[FHIRPlanDefinitionContact] | None = None
    editor: list[FHIRPlanDefinitionContact] | None = None
    reviewer: list[FHIRPlanDefinitionContact] | None = None
    endorser: list[FHIRPlanDefinitionContact] | None = None
    relatedArtifact: list[FHIRPlanDefinitionRelatedArtifact] | None = None
    library: list[str] | None = None
    goal: list[FHIRPlanDefinitionGoal] | None = None
    action: list[FHIRPlanDefinitionAction] | None = None


class PlainPlanDefinitionResponse(BaseModel):
    """Plain JSON representation of PlanDefinition."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Public sequence plan_definition_id.")
    url: str | None = None
    identifier: list[PlainPlanDefinitionIdentifier] | None = None
    version: str | None = None
    name: str | None = None
    title: str | None = None
    subtitle: str | None = None
    type: PlainPlanDefinitionSingleConcept | None = None
    status: str = Field(..., description="draft | active | retired | unknown.")
    experimental: bool | None = None
    subject_codeable_concept: PlainPlanDefinitionSingleConcept | None = None
    subject_reference: str | None = None
    subject_display: str | None = None
    date: dt.datetime | None = None
    publisher: str | None = None
    contact: list[PlainPlanDefinitionContact] | None = None
    description: str | None = None
    use_context: list[PlainPlanDefinitionUseContext] | None = None
    jurisdiction: list[PlainPlanDefinitionConcept] | None = None
    purpose: str | None = None
    usage: str | None = None
    copyright: str | None = None
    approval_date: dt.date | None = None
    last_review_date: dt.date | None = None
    effective_period_start: dt.datetime | None = None
    effective_period_end: dt.datetime | None = None
    topic: list[PlainPlanDefinitionConcept] | None = None
    author: list[PlainPlanDefinitionContact] | None = None
    editor: list[PlainPlanDefinitionContact] | None = None
    reviewer: list[PlainPlanDefinitionContact] | None = None
    endorser: list[PlainPlanDefinitionContact] | None = None
    related_artifact: list[PlainPlanDefinitionRelatedArtifact] | None = None
    library: list[str] | None = None
    goal: list[PlainPlanDefinitionGoal] | None = None
    action: list[PlainPlanDefinitionAction] | None = None

    extension: list[dict] | None = None
    created_by: str = Field(..., description="Creator user ID.")
    updated_by: str | None = Field(None, description="Last updater user ID.")
    created_at: dt.datetime = Field(..., description="Creation timestamp.")
    updated_at: dt.datetime = Field(..., description="Last update timestamp.")


class PaginatedPlanDefinitionResponse(BaseModel):
    """Paginated plain PlanDefinition list response."""

    model_config = ConfigDict(extra="allow")

    data: list[PlainPlanDefinitionResponse] = Field(..., description="List of plan definitions.")
    total: int | None = Field(None, description="Total matching records.")
    limit: int = Field(..., description="Page size.")
    offset: int = Field(..., description="Page offset.")


class FHIRPlanDefinitionBundleEntry(BaseModel):
    """Single entry in a PlanDefinition FHIR Bundle."""

    model_config = ConfigDict(extra="allow")

    fullUrl: str | None = Field(None, description="Full URL for resource.")
    resource: FHIRPlanDefinitionSchema = Field(..., description="PlanDefinition resource.")


class FHIRPlanDefinitionBundle(BaseModel):
    """FHIR R4 Bundle for PlanDefinition resources."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Bundle"] = "Bundle"
    type: str = Field("searchset", description="Bundle type.")
    total: int | None = Field(None, description="Total matching records.")
    entry: list[FHIRPlanDefinitionBundleEntry] = Field(
        default_factory=list, description="Bundle entries."
    )

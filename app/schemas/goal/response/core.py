from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    AuditFields,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)

from .category import PlainGoalCategory
from .identifier import PlainGoalIdentifier
from .note import FHIRGoalAnnotation, PlainGoalNote
from .reference import PlainGoalReference
from .target import FHIRGoalTarget, PlainGoalTarget


# ── FHIR JSON ─────────────────────────────────────────────────────────────────


class FHIRGoalSchema(BaseModel):
    """FHIR R4 Goal resource schema."""

    model_config = ConfigDict(populate_by_name=True)

    resourceType: Literal["Goal"] = "Goal"
    id: str = Field(..., description="Logical ID of this artifact.")
    meta: FHIRMeta | None = Field(None, description="Metadata about the resource.")
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External Ids for this goal."
    )
    lifecycleStatus: str = Field(
        ...,
        description="proposed | planned | accepted | active | on-hold | completed | cancelled | entered-in-error | rejected.",
    )
    achievementStatus: FHIRCodeableConcept | None = Field(
        None,
        description="in-progress | improving | worsening | no-change | achieved | sustaining | not-achieved | no-progress | not-attainable.",
    )
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="E.g. Treatment, dietary, behavioral, etc."
    )
    priority: FHIRCodeableConcept | None = Field(
        None, description="high-priority | moderate-priority | low-priority."
    )
    description: FHIRCodeableConcept = Field(
        ..., description="Code or text describing the goal."
    )
    subject: FHIRReference = Field(
        ..., description="Who this goal is intended for (Patient | Group | Organization)."
    )
    startDate: str | None = Field(
        None, description="When goal pursuit begins (date)."
    )
    startCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="When goal pursuit begins (CodeableConcept)."
    )
    target: list[FHIRGoalTarget] | None = Field(
        None, description="Target outcome for the goal."
    )
    statusDate: str | None = Field(
        None, description="When goal status took effect."
    )
    statusReason: str | None = Field(
        None, description="Reason for current status (string)."
    )
    expressedBy: FHIRReference | None = Field(
        None,
        description="Who's responsible for creating Goal (Patient | Practitioner | PractitionerRole | RelatedPerson).",
    )
    addresses: list[FHIRReference] | None = Field(
        None, description="Issues addressed by this goal."
    )
    note: list[FHIRGoalAnnotation] | None = Field(
        None, description="Comments about the goal."
    )
    outcomeCode: list[FHIRCodeableConcept] | None = Field(
        None, description="What result was achieved regarding the goal."
    )
    outcomeReference: list[FHIRReference] | None = Field(
        None, description="Observation that resulted from goal."
    )
    extension: list[dict] | None = Field(
        None, description="Additional content defined by implementations."
    )


class FHIRGoalBundleEntry(BaseModel):
    """Entry element within a FHIR searchset Bundle for Goal."""

    fullUrl: str = Field(..., description="Absolute URL for the resource.")
    resource: FHIRGoalSchema = Field(..., description="FHIR Goal resource.")


class FHIRGoalBundle(FHIRBundle):
    """FHIR R4 searchset Bundle for Goal resources."""

    entry: list[FHIRGoalBundleEntry] = Field(
        default_factory=list, description="Entries in this bundle page."
    )


# ── Plain JSON ────────────────────────────────────────────────────────────────


class PlainGoalResponse(AuditFields):
    """Plain snake_case serialization of a Goal entity."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Public sequence ID of the goal.")
    lifecycle_status: str = Field(..., description="Lifecycle status.")
    achievement_status: PlainGoalCategory | None = Field(
        None, description="Achievement status concept."
    )
    category: list[PlainGoalCategory] | None = Field(
        None, description="Categories."
    )
    priority: PlainGoalCategory | None = Field(
        None, description="Priority concept."
    )
    description: PlainGoalCategory | None = Field(
        None, description="Description concept."
    )
    subject: str = Field(..., description="Computed subject reference string.")
    subject_display: str | None = Field(None, description="Subject display text.")
    subject_type: str | None = Field(None, description="Subject resource type.")
    subject_id: int | None = Field(None, description="Subject public ID.")
    start_date: str | None = Field(None, description="Start date.")
    start_codeable_concept: PlainGoalCategory | None = Field(
        None, description="Start codeable concept."
    )
    target: list[PlainGoalTarget] | None = Field(
        None, description="Target outcomes."
    )
    status_date: str | None = Field(None, description="Status date.")
    status_reason: str | None = Field(None, description="Status reason string.")
    expressed_by: str | None = Field(
        None, description="Computed expressedBy reference string."
    )
    expressed_by_display: str | None = Field(
        None, description="ExpressedBy display text."
    )
    expressed_by_type: str | None = Field(
        None, description="ExpressedBy resource type."
    )
    expressed_by_id: int | None = Field(
        None, description="ExpressedBy public ID."
    )
    addresses: list[PlainGoalReference] | None = Field(
        None, description="Addresses references."
    )
    note: list[PlainGoalNote] | None = Field(
        None, description="Notes/annotations."
    )
    outcome_code: list[PlainGoalCategory] | None = Field(
        None, description="Outcome codes."
    )
    outcome_reference: list[PlainGoalReference] | None = Field(
        None, description="Outcome references."
    )
    identifier: list[PlainGoalIdentifier] | None = Field(
        None, description="Identifier child rows."
    )
    extension: list[dict] | None = Field(
        None, description="Extensions."
    )


class PaginatedGoalResponse(BaseModel):
    """Paginated plain JSON response for Goal list queries."""

    total: int = Field(..., description="Total matching records count.")
    limit: int = Field(..., description="Page size limit applied.")
    offset: int = Field(..., description="Offset applied.")
    data: list[PlainGoalResponse] = Field(
        default_factory=list, description="Page of Goal results."
    )

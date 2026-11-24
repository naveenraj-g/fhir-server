from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)
from app.schemas.datatypes.annotation import FHIRAnnotation
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRGoalTarget(BaseModel):
    measure: FHIRCodeableConcept | None = Field(
        None, description="The parameter whose value is being tracked."
    )
    detailQuantity: dict | None = Field(None, description="detail[x]: a Quantity.")
    detailRange: dict | None = Field(None, description="detail[x]: a Range.")
    detailCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="detail[x]: a CodeableConcept."
    )
    detailString: str | None = Field(None, description="detail[x]: a string.")
    detailBoolean: bool | None = Field(None, description="detail[x]: a boolean.")
    detailInteger: int | None = Field(None, description="detail[x]: an integer.")
    detailRatio: dict | None = Field(None, description="detail[x]: a Ratio.")
    dueDate: str | None = Field(None, description="due[x]: reach goal on this date.")
    dueDuration: dict | None = Field(
        None, description="due[x]: reach goal within this Duration."
    )


class FHIRGoalSchema(BaseModel):
    resourceType: str = Field("Goal", description="Always 'Goal'.")
    id: str = Field(..., description="Public goal_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External ids for this goal."
    )
    lifecycleStatus: str | None = Field(
        None,
        description="proposed | planned | accepted | active | on-hold | completed | cancelled | entered-in-error | rejected.",
    )
    achievementStatus: FHIRCodeableConcept | None = Field(
        None,
        description="in-progress | improving | worsening | no-change | achieved ...",
    )
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="E.g. Treatment, dietary, behavioral, etc."
    )
    priority: FHIRCodeableConcept | None = Field(
        None, description="high-priority | medium-priority | low-priority."
    )
    description: FHIRCodeableConcept | None = Field(
        None, description="Code or text describing the goal."
    )
    subject: FHIRReference | None = Field(
        None, description="Who this goal is intended for."
    )
    startDate: str | None = Field(
        None, description="start[x]: when goal pursuit begins."
    )
    startCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="start[x]: reference point for the goal."
    )
    target: list[FHIRGoalTarget] | None = Field(
        None, description="Target outcome for the goal."
    )
    statusDate: str | None = Field(
        None, description="When the goal status took effect."
    )
    statusReason: str | None = Field(None, description="Reason for the current status.")
    expressedBy: FHIRReference | None = Field(
        None, description="Who is responsible for creating the goal."
    )
    addresses: list[FHIRReference] | None = Field(
        None, description="Issues addressed by this goal."
    )
    note: list[FHIRAnnotation] | None = Field(
        None, description="Comments about the goal."
    )
    outcomeCode: list[FHIRCodeableConcept] | None = Field(
        None, description="What result was achieved regarding the goal."
    )
    outcomeReference: list[FHIRReference] | None = Field(
        None, description="Observation that resulted from goal."
    )


class FHIRGoalBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRGoalSchema | dict = Field(
        ...,
        description="A Goal (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Group / Organization (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRGoalBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRGoalBundleEntry] | None = None

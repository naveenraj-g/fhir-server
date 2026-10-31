from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.care_plan.response.activity import (
    FHIRCarePlanActivity,
    PlainCarePlanActivity,
)
from app.schemas.care_plan.response.identifier import PlainCarePlanIdentifier
from app.schemas.care_plan.response.note import PlainCarePlanNote
from app.schemas.datatypes import (
    AuditFields,
    FHIRBundle,
    FHIRBundleEntry,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
    PlainCodingRow,
)
from app.schemas.service_request.response.core import FHIRAnnotation


class FHIRCarePlanSchema(BaseModel):
    """FHIR R4 CarePlan resource representation."""

    model_config = ConfigDict(extra="forbid")

    resourceType: Literal["CarePlan"] = Field("CarePlan", description="Always 'CarePlan'.")
    id: str = Field(..., description="Public care_plan_id as a string.")
    meta: FHIRMeta | None = Field(None, description="Resource metadata.")
    extension: list[dict] | None = Field(None, description="Resource extensions.")
    identifier: list[FHIRIdentifier] | None = Field(None, description="External Ids for this plan.")
    instantiatesCanonical: list[str] | None = Field(None, description="Instantiates FHIR protocol or definition.")
    instantiatesUri: list[str] | None = Field(None, description="Instantiates external protocol or definition.")
    basedOn: list[FHIRReference] | None = Field(None, description="Fulfills CarePlan, ServiceRequest, or NutritionOrder.")
    replaces: list[FHIRReference] | None = Field(None, description="CarePlan replaced by this CarePlan.")
    partOf: list[FHIRReference] | None = Field(None, description="Part of referenced CarePlan.")
    status: str = Field(..., description="draft | active | on-hold | revoked | completed | entered-in-error | unknown.")
    intent: str = Field(..., description="proposal | plan | order | option.")
    category: list[FHIRCodeableConcept] | None = Field(None, description="Type of plan.")
    title: str | None = Field(None, description="Human-friendly name for the care plan.")
    description: str | None = Field(None, description="Summary of nature of plan.")
    subject: FHIRReference = Field(..., description="Who the care plan is for (Patient | Group).")
    encounter: FHIRReference | None = Field(None, description="Encounter created as part of.")
    period: FHIRPeriod | None = Field(None, description="Time period plan covers.")
    created: str | None = Field(None, description="Date record was first recorded.")
    author: FHIRReference | None = Field(None, description="Who is the designated responsible party.")
    contributor: list[FHIRReference] | None = Field(None, description="Who provided the content of the care plan.")
    careTeam: list[FHIRReference] | None = Field(None, description="Who's involved in plan.")
    addresses: list[FHIRReference] | None = Field(None, description="Health issues this plan addresses.")
    goal: list[FHIRReference] | None = Field(None, description="Desired outcome of plan.")
    activity: list[FHIRCarePlanActivity] | None = Field(None, description="Action to occur as part of plan.")
    note: list[FHIRAnnotation] | None = Field(None, description="Comments about the plan.")


class PlainCarePlanCategory(BaseModel):
    """Plain response shape for CarePlan.category."""

    model_config = ConfigDict(extra="allow")
    id: int | None = None
    text: str | None = None
    codings: list[PlainCodingRow] | None = None


class PlainCarePlanReference(BaseModel):
    """Plain response shape for a Reference child row."""

    model_config = ConfigDict(extra="allow")
    id: int | None = None
    reference: str | None = None
    type: str | None = None
    reference_id: int | None = None
    display: str | None = None


class PlainCarePlanResponse(AuditFields):
    """Plain snake_case response for CarePlan."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Public care_plan_id.")
    instantiates_canonical: list[str] | None = None
    instantiates_uri: list[str] | None = None
    status: str
    intent: str
    title: str | None = None
    description: str | None = None
    subject: str | None = None
    subject_id: int | None = None
    subject_type: str | None = None
    subject_display: str | None = None
    encounter: str | None = None
    encounter_id: int | None = None
    encounter_type: str | None = None
    encounter_display: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    created: datetime | None = None
    author: str | None = None
    author_id: int | None = None
    author_type: str | None = None
    author_display: str | None = None
    identifiers: list[PlainCarePlanIdentifier] | None = None
    categories: list[PlainCarePlanCategory] | None = None
    based_on: list[PlainCarePlanReference] | None = None
    replaces: list[PlainCarePlanReference] | None = None
    part_of: list[PlainCarePlanReference] | None = None
    contributors: list[PlainCarePlanReference] | None = None
    care_teams: list[PlainCarePlanReference] | None = None
    addresses: list[PlainCarePlanReference] | None = None
    goals: list[PlainCarePlanReference] | None = None
    activities: list[PlainCarePlanActivity] | None = None
    notes: list[PlainCarePlanNote] | None = None


class PaginatedCarePlanResponse(BaseModel):
    """Paginated plain snake_case response."""

    total: int | None = None
    limit: int
    offset: int
    data: list[PlainCarePlanResponse]


class FHIRCarePlanBundleEntry(FHIRBundleEntry):
    resource: FHIRCarePlanSchema | None = None


class FHIRCarePlanBundle(FHIRBundle):
    entry: list[FHIRCarePlanBundleEntry] | None = None

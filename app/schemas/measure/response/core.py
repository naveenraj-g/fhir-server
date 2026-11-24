from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRMeasureSchema(BaseModel):
    resourceType: str = Field("Measure", description="Always 'Measure'.")
    id: str = Field(..., description="Public measure_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    url: str | None = Field(None, description="Canonical identifier (a URI).")
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Additional identifier."
    )
    version: str | None = Field(None, description="Business version.")
    name: str | None = Field(None, description="Name (computer friendly).")
    title: str | None = Field(None, description="Name (human friendly).")
    subtitle: str | None = Field(None, description="Subordinate title.")
    status: str | None = Field(None, description="draft | active | retired | unknown.")
    experimental: bool | None = Field(
        None, description="For testing purposes, not real usage."
    )
    subjectCodeableConcept: FHIRCodeableConcept | None = Field(
        None,
        description="subject[x]: type of individual the measure is intended for.",
    )
    subjectReference: FHIRReference | None = Field(
        None, description="subject[x]: Reference(Group)."
    )
    date: str | None = Field(None, description="Date last changed.")
    publisher: str | None = Field(None, description="Name of the publisher.")
    contact: list[dict] | None = Field(
        None, description="Contact details for the publisher."
    )
    description: str | None = Field(None, description="Natural language description.")
    useContext: list[dict] | None = Field(
        None, description="The context that the content is intended to support."
    )
    jurisdiction: list[FHIRCodeableConcept] | None = Field(
        None, description="Intended jurisdiction."
    )
    purpose: str | None = Field(None, description="Why this measure is defined.")
    usage: str | None = Field(
        None, description="Describes the clinical usage of the measure."
    )
    copyright: str | None = Field(
        None, description="Use and/or publishing restrictions."
    )
    approvalDate: str | None = Field(
        None, description="When approved by the publisher."
    )
    lastReviewDate: str | None = Field(None, description="When last reviewed.")
    effectivePeriod: FHIRPeriod | None = Field(
        None, description="When expected to be used."
    )
    topic: list[FHIRCodeableConcept] | None = Field(
        None, description="E.g. Education, Treatment, Assessment."
    )
    author: list[dict] | None = Field(None, description="Who authored the content.")
    editor: list[dict] | None = Field(None, description="Who edited the content.")
    reviewer: list[dict] | None = Field(None, description="Who reviewed the content.")
    endorser: list[dict] | None = Field(None, description="Who endorsed the content.")
    relatedArtifact: list[dict] | None = Field(
        None, description="Additional documentation, citations, etc."
    )
    library: list[str] | None = Field(None, description="Logic used by the measure.")
    disclaimer: str | None = Field(
        None, description="Disclaimer for use of the measure."
    )
    scoring: FHIRCodeableConcept | None = Field(
        None, description="proportion | ratio | continuous-variable | cohort."
    )
    compositeScoring: FHIRCodeableConcept | None = Field(
        None, description="opportunity | all-or-nothing | linear | weighted."
    )
    type: list[FHIRCodeableConcept] | None = Field(
        None,
        description="process | outcome | structure | patient-reported-outcome | composite.",
    )
    riskAdjustment: str | None = Field(
        None, description="How risk adjustment is applied."
    )
    rateAggregation: str | None = Field(
        None, description="How is rate aggregation performed."
    )
    rationale: str | None = Field(
        None, description="Detailed description of why the measure exists."
    )
    clinicalRecommendationStatement: str | None = Field(
        None, description="Summary of clinical guidelines."
    )
    improvementNotation: FHIRCodeableConcept | None = Field(
        None, description="increase | decrease."
    )
    definition: list[str] | None = Field(
        None, description="Defined terms used in the measure documentation."
    )
    guidance: str | None = Field(
        None, description="Additional guidance for implementers."
    )
    group: list[dict] | None = Field(None, description="Population criteria group.")
    supplementalData: list[dict] | None = Field(
        None, description="What other data should be reported."
    )


class FHIRMeasureBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRMeasureSchema | dict = Field(
        ...,
        description="A Measure (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRMeasureBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRMeasureBundleEntry] | None = None

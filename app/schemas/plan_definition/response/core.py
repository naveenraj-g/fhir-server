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


class FHIRPlanDefinitionSchema(BaseModel):
    resourceType: str = Field("PlanDefinition", description="Always 'PlanDefinition'.")
    id: str = Field(..., description="Public plan_definition_id as a string.")
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
    type: FHIRCodeableConcept | None = Field(
        None,
        description="order-set | clinical-protocol | eca-rule | workflow-definition.",
    )
    status: str | None = Field(None, description="draft | active | retired | unknown.")
    experimental: bool | None = Field(
        None, description="For testing purposes, not real usage."
    )
    subjectCodeableConcept: FHIRCodeableConcept | None = Field(
        None,
        description="subject[x]: type of individual the plan definition is intended for.",
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
    purpose: str | None = Field(
        None, description="Why this plan definition is defined."
    )
    usage: str | None = Field(
        None, description="Describes the clinical usage of the plan definition."
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
    library: list[str] | None = Field(
        None, description="Logic used by the plan definition."
    )
    goal: list[dict] | None = Field(
        None, description="What the plan is trying to accomplish."
    )
    action: list[dict] | None = Field(None, description="Action defined by the plan.")


class FHIRPlanDefinitionBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRPlanDefinitionSchema | dict = Field(
        ...,
        description="A PlanDefinition (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRPlanDefinitionBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRPlanDefinitionBundleEntry] | None = None

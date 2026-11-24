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


class FHIRActivityDefinitionSchema(BaseModel):
    resourceType: str = Field(
        "ActivityDefinition", description="Always 'ActivityDefinition'."
    )
    id: str = Field(..., description="Public activity_definition_id as a string.")
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
        description="subject[x]: type of individual the activity definition is intended for.",
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
        None, description="Why this activity definition is defined."
    )
    usage: str | None = Field(
        None, description="Describes the clinical usage of the activity definition."
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
        None, description="Logic used by the activity definition."
    )
    kind: str | None = Field(None, description="Kind of resource.")
    profile: str | None = Field(
        None, description="What profile the resource needs to conform to."
    )
    code: FHIRCodeableConcept | None = Field(
        None, description="Detail type of activity."
    )
    intent: str | None = Field(
        None, description="proposal | plan | directive | order | ... | option."
    )
    priority: str | None = Field(None, description="routine | urgent | asap | stat.")
    doNotPerform: bool | None = Field(
        None, description="True if the activity should not be performed."
    )
    timingTiming: dict | None = Field(None, description="timing[x]: Timing.")
    timingDateTime: str | None = Field(None, description="timing[x]: dateTime.")
    timingAge: dict | None = Field(None, description="timing[x]: Age.")
    timingPeriod: FHIRPeriod | None = Field(None, description="timing[x]: Period.")
    timingRange: dict | None = Field(None, description="timing[x]: Range.")
    timingDuration: dict | None = Field(None, description="timing[x]: Duration.")
    location: FHIRReference | None = Field(None, description="Where it should happen.")
    participant: list[dict] | None = Field(
        None, description="Who should participate in the action."
    )
    productReference: FHIRReference | None = Field(
        None, description="product[x]: Reference(Medication | Substance)."
    )
    productCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="product[x]: CodeableConcept."
    )
    quantity: dict | None = Field(
        None, description="How much is administered/consumed/supplied."
    )
    dosage: list[dict] | None = Field(None, description="Detailed dosage instructions.")
    bodySite: list[FHIRCodeableConcept] | None = Field(
        None, description="What part of body to perform on."
    )
    specimenRequirement: list[FHIRReference] | None = Field(
        None, description="What specimens are required."
    )
    observationRequirement: list[FHIRReference] | None = Field(
        None, description="What observations are required."
    )
    observationResultRequirement: list[FHIRReference] | None = Field(
        None, description="What observations must be produced."
    )
    transform: str | None = Field(None, description="Transform to apply the template.")
    dynamicValue: list[dict] | None = Field(
        None, description="Dynamic aspects of the definition."
    )


class FHIRActivityDefinitionBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRActivityDefinitionSchema | dict = Field(
        ...,
        description="An ActivityDefinition (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRActivityDefinitionBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRActivityDefinitionBundleEntry] | None = None

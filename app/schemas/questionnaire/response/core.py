from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRCoding,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRQuestionnaireItem(BaseModel):
    linkId: str | None = Field(None, description="Unique id for the item.")
    definition: str | None = Field(
        None, description="ElementDefinition this item corresponds to."
    )
    code: list[FHIRCoding] | None = Field(
        None, description="Corresponding concept for this item in a terminology."
    )
    prefix: str | None = Field(None, description="E.g. '1(a)', '2.5.3'.")
    text: str | None = Field(None, description="Primary text for the item.")
    type: str | None = Field(
        None,
        description="group | display | boolean | decimal | integer | date | dateTime | time | string | text | url | choice | open-choice | attachment | reference | quantity.",
    )
    enableWhen: list[dict] | None = Field(
        None, description="Only allow data when: [{question, operator, answer[x]}]."
    )
    enableBehavior: str | None = Field(None, description="all | any.")
    required: bool | None = Field(
        None, description="Whether the item must be answered."
    )
    repeats: bool | None = Field(None, description="Whether the item may repeat.")
    readOnly: bool | None = Field(None, description="Don't allow human editing.")
    maxLength: int | None = Field(
        None, description="No more than this many characters."
    )
    answerValueSet: str | None = Field(
        None, description="Valueset containing permitted answers."
    )
    answerOption: list[dict] | None = Field(
        None, description="Permitted answers: [{value[x], initialSelected}]."
    )
    initial: list[dict] | None = Field(
        None, description="Initial value(s) when item is first rendered: [{value[x]}]."
    )
    item: list[FHIRQuestionnaireItem] | None = Field(
        None, description="Nested questionnaire items."
    )


FHIRQuestionnaireItem.model_rebuild()


class FHIRQuestionnaireSchema(BaseModel):
    resourceType: str = Field("Questionnaire", description="Always 'Questionnaire'.")
    id: str = Field(..., description="Public questionnaire_id as a string.")
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
        None, description="Additional identifier for the questionnaire."
    )
    version: str | None = Field(None, description="Business version.")
    name: str | None = Field(None, description="Name (computer friendly).")
    title: str | None = Field(None, description="Name (human friendly).")
    derivedFrom: list[str] | None = Field(
        None, description="Instantiates protocol or definition."
    )
    status: str | None = Field(None, description="draft | active | retired | unknown.")
    experimental: bool | None = Field(None, description="For testing purposes.")
    subjectType: list[str] | None = Field(
        None, description="Resource types that can be the subject."
    )
    date: str | None = Field(None, description="Date last changed.")
    publisher: str | None = Field(None, description="Name of the publisher.")
    contact: list[dict] | None = Field(
        None, description="Contact details: [{name, telecom}]."
    )
    description: str | None = Field(None, description="Natural language description.")
    useContext: list[dict] | None = Field(
        None, description="The context the content is intended to support."
    )
    jurisdiction: list[FHIRCodeableConcept] | None = Field(
        None, description="Intended jurisdiction."
    )
    purpose: str | None = Field(None, description="Why this questionnaire is defined.")
    copyright: str | None = Field(
        None, description="Use and/or publishing restrictions."
    )
    approvalDate: str | None = Field(
        None, description="When approved by the publisher."
    )
    lastReviewDate: str | None = Field(None, description="When last reviewed.")
    effectivePeriod: FHIRPeriod | None = Field(
        None, description="When the questionnaire is expected to be used."
    )
    code: list[FHIRCoding] | None = Field(
        None, description="Concept that represents the overall questionnaire."
    )
    item: list[FHIRQuestionnaireItem] | None = Field(
        None, description="Questions and sections within the Questionnaire."
    )


class FHIRQuestionnaireBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRQuestionnaireSchema | dict = Field(
        ...,
        description="A Questionnaire (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRQuestionnaireBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRQuestionnaireBundleEntry] | None = None

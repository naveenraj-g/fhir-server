from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCoding,
    FHIRIdentifier,
    FHIRMeta,
    FHIRQuantity,
    FHIRReference,
)
from app.schemas.datatypes.attachment import FHIRAttachment
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRQuestionnaireResponseAnswer(BaseModel):
    valueBoolean: bool | None = Field(
        None, description="Single-valued answer: boolean."
    )
    valueDecimal: float | None = Field(
        None, description="Single-valued answer: decimal."
    )
    valueInteger: int | None = Field(None, description="Single-valued answer: integer.")
    valueDate: str | None = Field(None, description="Single-valued answer: date.")
    valueDateTime: str | None = Field(
        None, description="Single-valued answer: dateTime."
    )
    valueTime: str | None = Field(None, description="Single-valued answer: time.")
    valueString: str | None = Field(None, description="Single-valued answer: string.")
    valueUri: str | None = Field(None, description="Single-valued answer: uri.")
    valueAttachment: FHIRAttachment | None = Field(
        None, description="Single-valued answer: Attachment."
    )
    valueCoding: FHIRCoding | None = Field(
        None, description="Single-valued answer: Coding."
    )
    valueQuantity: FHIRQuantity | None = Field(
        None, description="Single-valued answer: Quantity."
    )
    valueReference: FHIRReference | None = Field(
        None, description="Single-valued answer: Reference(Any)."
    )
    item: list[FHIRQuestionnaireResponseItem] | None = Field(
        None, description="Nested groups and questions beneath this answer."
    )


class FHIRQuestionnaireResponseItem(BaseModel):
    linkId: str | None = Field(
        None, description="The linkId of the Questionnaire item this answers."
    )
    definition: str | None = Field(
        None, description="ElementDefinition this item corresponds to."
    )
    text: str | None = Field(None, description="Name for group or question text.")
    answer: list[FHIRQuestionnaireResponseAnswer] | None = Field(
        None, description="The response(s) to the question."
    )
    item: list[FHIRQuestionnaireResponseItem] | None = Field(
        None, description="Nested questionnaire response items."
    )


FHIRQuestionnaireResponseAnswer.model_rebuild()
FHIRQuestionnaireResponseItem.model_rebuild()


class FHIRQuestionnaireResponseSchema(BaseModel):
    resourceType: str = Field(
        "QuestionnaireResponse", description="Always 'QuestionnaireResponse'."
    )
    id: str = Field(..., description="Public questionnaire_response_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: FHIRIdentifier | None = Field(
        None, description="Unique id for this set of answers."
    )
    basedOn: list[FHIRReference] | None = Field(
        None, description="Request fulfilled by this QuestionnaireResponse."
    )
    partOf: list[FHIRReference] | None = Field(None, description="Part of this action.")
    questionnaire: str | None = Field(
        None, description="Form being answered (a canonical URL)."
    )
    status: str | None = Field(
        None,
        description="in-progress | completed | amended | entered-in-error | stopped.",
    )
    subject: FHIRReference | None = Field(
        None, description="The subject of the questions."
    )
    encounter: FHIRReference | None = Field(
        None, description="Encounter created as part of."
    )
    authored: str | None = Field(None, description="Date the answers were gathered.")
    author: FHIRReference | None = Field(
        None, description="Person who received and recorded the answers."
    )
    source: FHIRReference | None = Field(
        None, description="The person who answered the questions."
    )
    item: list[FHIRQuestionnaireResponseItem] | None = Field(
        None, description="Groups and questions with their answers."
    )


class FHIRQuestionnaireResponseBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRQuestionnaireResponseSchema | dict = Field(
        ...,
        description="A QuestionnaireResponse (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Practitioner / PractitionerRole / RelatedPerson / Organization / Encounter / CarePlan / ServiceRequest / Observation / Procedure (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRQuestionnaireResponseBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRQuestionnaireResponseBundleEntry] | None = None

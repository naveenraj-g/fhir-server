from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirCodingInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
)

# publication-status (the required binding of Questionnaire.status).
StatusCode = Literal["draft", "active", "retired", "unknown"]
# item-type (the required binding of Questionnaire.item.type).
ItemTypeCode = Literal[
    "group",
    "display",
    "boolean",
    "decimal",
    "integer",
    "date",
    "dateTime",
    "time",
    "string",
    "text",
    "url",
    "choice",
    "open-choice",
    "attachment",
    "reference",
    "quantity",
]
EnableBehaviorCode = Literal["all", "any"]

_EXAMPLE = {
    "resourceType": "Questionnaire",
    "url": "https://fhir-server.dev/fhir/Questionnaire/phq-9",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/questionnaire-id",
            "value": "PHQ-9",
        }
    ],
    "version": "1.0",
    "name": "PHQ9",
    "title": "Patient Health Questionnaire 9",
    "status": "active",
    "subjectType": ["Patient"],
    "date": "2026-01-15",
    "publisher": "Example Health",
    "description": "A nine-question depression screen.",
    "useContext": [
        {
            "code": {
                "system": "http://terminology.hl7.org/CodeSystem/usage-context-type",
                "code": "focus",
            },
            "valueCodeableConcept": {
                "coding": [{"system": "http://snomed.info/sct", "code": "35489007"}]
            },
        }
    ],
    "jurisdiction": [{"coding": [{"system": "urn:iso:std:iso:3166", "code": "US"}]}],
    "effectivePeriod": {"start": "2026-01-01"},
    "code": [{"system": "http://loinc.org", "code": "44249-1"}],
    "item": [
        {
            "linkId": "1",
            "text": "Mood",
            "type": "group",
            "item": [
                {
                    "linkId": "1.1",
                    "definition": "http://example.org/definitions/interest",
                    "code": [{"system": "http://loinc.org", "code": "44250-9"}],
                    "text": "Little interest or pleasure in doing things",
                    "type": "choice",
                    "required": True,
                    "answerOption": [
                        {
                            "valueCoding": {
                                "system": "http://loinc.org",
                                "code": "LA6568-5",
                            }
                        }
                    ],
                }
            ],
        }
    ],
}


class QuestionnaireItemInput(FhirInputModel):
    """Questionnaire.item - a group or question, nested to any depth. Self-referential, so it is
    rebuilt at the bottom of this module. Only `item.code` and `item.definition` are searchable
    (`code`, `definition`); the rest lives only in `content`."""

    linkId: str | None = Field(
        None,
        description="Unique id for the item within the questionnaire (required by R4).",
    )
    definition: str | None = Field(
        None,
        description="ElementDefinition this item corresponds to (a uri). Searched by `definition`.",
    )
    code: list[FhirCodingInput] | None = Field(
        None,
        description="Corresponding concept for this item in a terminology. Searched by `code`.",
    )
    prefix: str | None = Field(None, description="E.g. '1(a)', '2.5.3'.")
    text: str | None = Field(None, description="Primary text for the item.")
    type: ItemTypeCode | None = Field(
        None,
        description="group | display | boolean | decimal | integer | date | dateTime | time | string | text | url | choice | open-choice | attachment | reference | quantity (required by R4).",
    )
    enableWhen: list[dict] | None = Field(
        None,
        description="Only allow data when: [{question, operator (exists | = | != | > | < | >= | <=), answer[x]}] - answer[x] is one of answerBoolean, answerDecimal, answerInteger, answerDate, answerDateTime, answerTime, answerString, answerCoding, answerQuantity, answerReference.",
    )
    enableBehavior: EnableBehaviorCode | None = Field(
        None, description="all | any - whether all or any enableWhen must be true."
    )
    required: bool | None = Field(
        None, description="Whether the item must be answered."
    )
    repeats: bool | None = Field(None, description="Whether the item may repeat.")
    readOnly: bool | None = Field(None, description="Don't allow human editing.")
    maxLength: int | None = Field(
        None, description="No more than this many characters."
    )
    answerValueSet: str | None = Field(
        None, description="Valueset containing permitted answers (a canonical URL)."
    )
    answerOption: list[dict] | None = Field(
        None,
        description="Permitted answers: [{value[x], initialSelected}] - value[x] is one of valueInteger, valueDate, valueTime, valueString, valueCoding, valueReference.",
    )
    initial: list[dict] | None = Field(
        None,
        description="Initial value(s) when item is first rendered: [{value[x]}] - one of valueBoolean, valueDecimal, valueInteger, valueDate, valueDateTime, valueTime, valueString, valueUri, valueAttachment, valueCoding, valueQuantity, valueReference.",
    )
    item: list[QuestionnaireItemInput] | None = Field(
        None, description="Nested questionnaire items."
    )


QuestionnaireItemInput.model_rebuild()


class _QuestionnaireFields(FhirInputModel):
    """Every writable Questionnaire element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/questionnaire.html). Create and patch accept exactly the same
    fields. R4 requires only `status`, but only the java_validator backend enforces cardinality
    minimums.

    The validated body is stored whole (QuestionnaireModel.content), so any valid R4 element is
    kept - including ones this model does not declare. Server-managed elements are ignored if
    sent: `id` (assigned from the questionnaire_id sequence) and `meta` (audit/tenant data,
    stamped on at read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Questionnaire"] | None = Field(
        None, description="Optional; if supplied it must be 'Questionnaire'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    url: str | None = Field(
        None,
        description="Canonical identifier for this questionnaire, represented as a URI (globally unique). Searched by `url`.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None,
        description="Additional identifier for the questionnaire. Searched by `identifier`.",
    )
    version: str | None = Field(
        None,
        description="Business version of the questionnaire. Searched by `version`.",
    )
    name: str | None = Field(
        None,
        description="Name for this questionnaire (computer friendly). Searched by `name`.",
    )
    title: str | None = Field(
        None,
        description="Name for this questionnaire (human friendly). Searched by `title`.",
    )
    derivedFrom: list[str] | None = Field(
        None, description="Instantiates protocol or definition (canonical URLs)."
    )
    status: StatusCode | None = Field(
        None,
        description="draft | active | retired | unknown (required by R4). Searched by `status`.",
    )
    experimental: bool | None = Field(
        None, description="For testing purposes, not real usage."
    )
    subjectType: list[str] | None = Field(
        None,
        description="Resource types (e.g. 'Patient') that can be the subject of QuestionnaireResponse. Searched by `subject-type`.",
    )
    date: str | None = Field(
        None,
        description="Date last changed (a FHIR dateTime, possibly partial). Searched by `date`.",
    )
    publisher: str | None = Field(
        None,
        description="Name of the publisher (organization or individual). Searched by `publisher`.",
    )
    contact: list[dict] | None = Field(
        None,
        description="Contact details for the publisher: [{name, telecom: [ContactPoint]}].",
    )
    description: str | None = Field(
        None,
        description="Natural language description of the questionnaire (markdown). Searched by `description`.",
    )
    useContext: list[dict] | None = Field(
        None,
        description="The context that the content is intended to support: [{code (Coding), value[x]}] where value[x] is valueCodeableConcept, valueQuantity, valueRange or valueReference. Searched by `context-type`, `context`, `context-quantity` and the `context-type-value` / `context-type-quantity` composites.",
    )
    jurisdiction: list[FhirCodeableConceptInput] | None = Field(
        None,
        description="Intended jurisdiction for the questionnaire. Searched by `jurisdiction`.",
    )
    purpose: str | None = Field(
        None, description="Why this questionnaire is defined (markdown)."
    )
    copyright: str | None = Field(
        None, description="Use and/or publishing restrictions (markdown)."
    )
    approvalDate: str | None = Field(
        None, description="When the questionnaire was approved by the publisher."
    )
    lastReviewDate: str | None = Field(
        None, description="When the questionnaire was last reviewed."
    )
    effectivePeriod: FhirPeriodInput | None = Field(
        None,
        description="When the questionnaire is expected to be used. Searched by `effective`.",
    )
    code: list[FhirCodingInput] | None = Field(
        None,
        description="Concept that represents the overall questionnaire (not searchable: `code` reads item.code).",
    )
    item: list[QuestionnaireItemInput] | None = Field(
        None,
        description="Questions and sections within the Questionnaire, nested to any depth. Only item.code and item.definition are searchable.",
    )


class QuestionnaireCreateSchema(_QuestionnaireFields):
    """POST body - a FHIR R4 Questionnaire resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class QuestionnairePatchSchema(_QuestionnaireFields):
    """PATCH body - a partial FHIR R4 Questionnaire (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale - a list (even `[]`) replaces every existing entry,
    an object such as `effectivePeriod` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "retired",
                "title": "Patient Health Questionnaire 9 (retired)",
            }
        }
    }

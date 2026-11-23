from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirAttachmentInput,
    FhirCodingInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirReferenceInput,
)

# questionnaire-answers-status (the required binding of QuestionnaireResponse.status).
StatusCode = Literal[
    "in-progress", "completed", "amended", "entered-in-error", "stopped"
]

_EXAMPLE = {
    "resourceType": "QuestionnaireResponse",
    "identifier": {
        "system": "https://fhir-server.dev/fhir/identifier-system/questionnaire-response-id",
        "value": "QR-1001",
    },
    "questionnaire": "https://fhir-server.dev/fhir/Questionnaire/phq-9",
    "status": "completed",
    "subject": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "authored": "2026-02-01T10:00:00Z",
    "author": {"reference": "Practitioner/30001"},
    "source": {"reference": "Patient/10001"},
    "item": [
        {
            "linkId": "1",
            "text": "Mood",
            "item": [
                {
                    "linkId": "1.1",
                    "text": "Little interest or pleasure in doing things",
                    "answer": [{"valueInteger": 2}],
                }
            ],
        }
    ],
}


class QuestionnaireResponseAnswerInput(FhirInputModel):
    """QuestionnaireResponse.item.answer - one answer. `value[x]` is one of the typed values below
    (R4 allows at most one); `item` nests further items beneath this answer. Mutually recursive with
    QuestionnaireResponseItemInput, so both are rebuilt at the bottom of this module."""

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
    valueAttachment: FhirAttachmentInput | None = Field(
        None, description="Single-valued answer: Attachment."
    )
    valueCoding: FhirCodingInput | None = Field(
        None, description="Single-valued answer: Coding."
    )
    valueQuantity: dict | None = Field(
        None,
        description="Single-valued answer: Quantity ({value, comparator, unit, system, code}).",
    )
    valueReference: FhirReferenceInput | None = Field(
        None,
        description="Single-valued answer: Reference(Any). A relative reference to a resource this server has must exist in the caller's org (422 otherwise).",
    )
    item: list[QuestionnaireResponseItemInput] | None = Field(
        None, description="Nested groups and questions beneath this answer."
    )


class QuestionnaireResponseItemInput(FhirInputModel):
    """QuestionnaireResponse.item - a group or question's answers, nested to any depth (R4 rule
    qrs-1: an item has `item` or `answer`, not both - enforced by the java_validator backend)."""

    linkId: str | None = Field(
        None,
        description="The linkId of the Questionnaire item this answers (required by R4).",
    )
    definition: str | None = Field(
        None, description="ElementDefinition this item corresponds to (a uri)."
    )
    text: str | None = Field(None, description="Name for group or question text.")
    answer: list[QuestionnaireResponseAnswerInput] | None = Field(
        None, description="The response(s) to the question."
    )
    item: list[QuestionnaireResponseItemInput] | None = Field(
        None, description="Nested questionnaire response items."
    )


QuestionnaireResponseAnswerInput.model_rebuild()
QuestionnaireResponseItemInput.model_rebuild()


class _QuestionnaireResponseFields(FhirInputModel):
    """Every writable QuestionnaireResponse element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/questionnaireresponse.html). Create and patch accept exactly the
    same fields. R4 requires only `status`, but only the java_validator backend enforces cardinality
    minimums.

    The validated body is stored whole (QuestionnaireResponseModel.content), so any valid R4
    element is kept - including ones this model does not declare. Server-managed elements are
    ignored if sent: `id` (assigned from the questionnaire_response_id sequence) and `meta`
    (audit/tenant data, stamped on at read time). org_id and created_by/updated_by come from the
    verified JWT (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["QuestionnaireResponse"] | None = Field(
        None, description="Optional; if supplied it must be 'QuestionnaireResponse'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: FhirIdentifierInput | None = Field(
        None,
        description="Unique id for this set of answers (0..1 in R4). Searched by `identifier`.",
    )
    basedOn: list[FhirReferenceInput] | None = Field(
        None,
        description="Request fulfilled by this QuestionnaireResponse - Reference(CarePlan | ServiceRequest). A relative reference must exist in the caller's org (422 otherwise). Searched by `based-on`.",
    )
    partOf: list[FhirReferenceInput] | None = Field(
        None,
        description="Part of this action - Reference(Observation | Procedure). A relative reference must exist in the caller's org (422 otherwise). Searched by `part-of`.",
    )
    questionnaire: str | None = Field(
        None,
        description="Form being answered - the canonical URL of a Questionnaire, optionally versioned (`url|1.0`). Searched by `questionnaire`.",
    )
    status: StatusCode | None = Field(
        None,
        description="in-progress | completed | amended | entered-in-error | stopped (required by R4). Searched by `status`.",
    )
    subject: FhirReferenceInput | None = Field(
        None,
        description="The subject of the questions - Reference(Any). A relative reference to a resource this server has must exist in the caller's org (422 otherwise). Searched by `subject` / `patient`.",
    )
    encounter: FhirReferenceInput | None = Field(
        None,
        description="Encounter created as part of - Reference(Encounter). A relative reference must exist in the caller's org (422 otherwise). Searched by `encounter`.",
    )
    authored: str | None = Field(
        None,
        description="Date the answers were gathered (a FHIR dateTime). Searched by `authored`.",
    )
    author: FhirReferenceInput | None = Field(
        None,
        description="Person who received and recorded the answers - Reference(Device | Practitioner | PractitionerRole | Patient | RelatedPerson | Organization). A relative reference must exist in the caller's org (422 otherwise). Searched by `author`.",
    )
    source: FhirReferenceInput | None = Field(
        None,
        description="The person who answered the questions - Reference(Patient | Practitioner | PractitionerRole | RelatedPerson). A relative reference must exist in the caller's org (422 otherwise). Searched by `source`.",
    )
    item: list[QuestionnaireResponseItemInput] | None = Field(
        None,
        description="Groups and questions with their answers, nested to any depth. Not searchable (R4 defines no item search parameter): stored only in `content`.",
    )


class QuestionnaireResponseCreateSchema(_QuestionnaireResponseFields):
    """POST body - a FHIR R4 QuestionnaireResponse resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class QuestionnaireResponsePatchSchema(_QuestionnaireResponseFields):
    """PATCH body - a partial FHIR R4 QuestionnaireResponse (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale - a list (even `[]`) replaces every existing entry,
    an object such as `subject` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "amended",
                "item": [{"linkId": "1", "answer": [{"valueString": "corrected"}]}],
            }
        }
    }

"""FHIR camelCase (BackboneElement) types for Questionnaire.item and its
3 BackboneElement children. Not in app.schemas.datatypes — these are
Questionnaire-specific shapes (same situation as app.schemas.encounter.response.FHIRDuration).

Every choice-type field (`answer[x]`, `value[x]`) is rendered as separate,
individually-optional camelCase keys (answerBoolean, answerCoding,
answerQuantity, ...) — the real FHIR R4 JSON wire shape for a choice type —
rather than collapsed into one polymorphic field, since exactly one is
ever populated and each has a genuinely different JSON type."""

from __future__ import annotations

from datetime import date, datetime, time

from pydantic import BaseModel, Field

from app.schemas.datatypes import FHIRAttachment, FHIRCoding, FHIRReference

from .fhir_quantity import FHIRQuantity


class FHIRQuestionnaireItemEnableWhen(BaseModel):
    question: str
    operator: str
    answerBoolean: bool | None = None
    answerDecimal: float | None = None
    answerInteger: int | None = None
    answerDate: date | None = None
    answerDateTime: datetime | None = None
    answerTime: time | None = None
    answerString: str | None = None
    answerCoding: FHIRCoding | None = None
    answerQuantity: FHIRQuantity | None = None
    answerReference: FHIRReference | None = None


class FHIRQuestionnaireItemAnswerOption(BaseModel):
    valueInteger: int | None = None
    valueDate: date | None = None
    valueTime: time | None = None
    valueString: str | None = None
    valueCoding: FHIRCoding | None = None
    valueReference: FHIRReference | None = None
    initialSelected: bool | None = None


class FHIRQuestionnaireItemInitial(BaseModel):
    valueBoolean: bool | None = None
    valueDecimal: float | None = None
    valueInteger: int | None = None
    valueDate: date | None = None
    valueDateTime: datetime | None = None
    valueTime: time | None = None
    valueString: str | None = None
    valueUri: str | None = None
    valueAttachment: FHIRAttachment | None = None
    valueCoding: FHIRCoding | None = None
    valueQuantity: FHIRQuantity | None = None
    valueReference: FHIRReference | None = None


class FHIRQuestionnaireItem(BaseModel):
    """Recursive — `item` nests to unbounded depth. Must call
    `model_rebuild()` after class definition."""

    linkId: str
    definition: str | None = None
    code: list[FHIRCoding] | None = None
    prefix: str | None = None
    text: str | None = None
    type: str
    enableWhen: list[FHIRQuestionnaireItemEnableWhen] | None = None
    enableBehavior: str | None = None
    required: bool | None = None
    repeats: bool | None = None
    readOnly: bool | None = None
    maxLength: int | None = None
    answerValueSet: str | None = None
    answerOption: list[FHIRQuestionnaireItemAnswerOption] | None = None
    initial: list[FHIRQuestionnaireItemInitial] | None = None
    item: list[FHIRQuestionnaireItem] | None = Field(None, description="Nested questions/groups.")


FHIRQuestionnaireItem.model_rebuild()

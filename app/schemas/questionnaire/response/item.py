from __future__ import annotations

from pydantic import Field

from app.schemas.datatypes import AuditFields, PlainCodingRow

from .item_answer_option import PlainQuestionnaireItemAnswerOption
from .item_enable_when import PlainQuestionnaireItemEnableWhen
from .item_initial import PlainQuestionnaireItemInitial


class PlainQuestionnaireItem(AuditFields):
    """Recursive — `item` nests to unbounded depth, mirroring
    app.schemas.questionnaire.input.item.QuestionnaireItemInput. Must call
    `model_rebuild()` after class definition (see CLAUDE.md's Schema
    Conventions section)."""

    id: int = Field(..., description="Internal row ID.")
    link_id: str = Field(..., description="Unique id for this item within the questionnaire.")
    definition: str | None = Field(None, description="ElementDefinition reference (uri).")
    codings: list[PlainCodingRow] | None = Field(None, description="Terminology code(s) for this item.")
    prefix: str | None = Field(None, description="A short label, e.g. '1(a)'.")
    text: str | None = Field(None, description="Primary text for the item.")
    type: str = Field(..., description="group | display | boolean | ... | quantity.")
    enable_whens: list[PlainQuestionnaireItemEnableWhen] | None = Field(
        None, description="Conditions for enabling the item."
    )
    enable_behavior: str | None = Field(None, description="all | any.")
    required: bool | None = Field(None, description="Must be present in a completed response.")
    repeats: bool | None = Field(None, description="May occur multiple times.")
    read_only: bool | None = Field(None, description="Respondent cannot change the value.")
    max_length: int | None = Field(None, description="Maximum characters for a valid answer.")
    answer_value_set: str | None = Field(None, description="Canonical reference to the permitted-answers ValueSet.")
    answer_options: list[PlainQuestionnaireItemAnswerOption] | None = Field(
        None, description="Permitted answer values."
    )
    initials: list[PlainQuestionnaireItemInitial] | None = Field(
        None, description="Pre-populated initial value(s)."
    )
    item: list[PlainQuestionnaireItem] | None = Field(
        None, description="Nested questions/groups beneath this one."
    )


PlainQuestionnaireItem.model_rebuild()

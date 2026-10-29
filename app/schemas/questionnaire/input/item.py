from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput
from app.schemas.enums import QuestionnaireEnableBehavior, QuestionnaireItemType

from .item_answer_option import QuestionnaireItemAnswerOptionInput
from .item_enable_when import QuestionnaireItemEnableWhenInput
from .item_initial import QuestionnaireItemInitialInput


class QuestionnaireItemInput(BaseModel):
    """Questionnaire.item (0..*, recursive — `item` nests to unbounded
    depth, per the spec's own `item.item` self-reference). Recursive
    Pydantic schema — must call `model_rebuild()` after class definition
    (see CLAUDE.md's Schema Conventions section) so the `list["QuestionnaireItemInput"]`
    forward reference below resolves."""

    model_config = ConfigDict(extra="forbid")

    link_id: str = Field(
        ..., description="Unique id for this particular item in this questionnaire, used to link to a QuestionnaireResponse."
    )
    definition: str | None = Field(
        None,
        description="ElementDefinition reference (uri) supplying default code/type/required/repeats/maxLength/binding for this item.",
    )
    code: list[CodingInput] | None = Field(
        None, description="Terminology code(s) for this item (e.g. LOINC)."
    )
    prefix: str | None = Field(
        None, description="A short label for a particular group, question, or set of display text, e.g. '1(a)'."
    )
    text: str | None = Field(
        None, description="Primary text for the item (section name, question text, or display text)."
    )
    type: QuestionnaireItemType = Field(
        ...,
        description="group | display | boolean | decimal | integer | date | dateTime | time | string | text | url | choice | open-choice | attachment | reference | quantity.",
    )
    enable_when: list[QuestionnaireItemEnableWhenInput] | None = Field(
        None, description="Only allow data when conditions are met."
    )
    enable_behavior: QuestionnaireEnableBehavior | None = Field(
        None,
        description="all | any — controls how multiple enable_when values are interpreted. Required if enable_when has more than one entry.",
    )
    required: bool | None = Field(
        None, description="Whether the item must be included in data results."
    )
    repeats: bool | None = Field(
        None, description="Whether the item may repeat."
    )
    read_only: bool | None = Field(
        None, description="Don't allow human editing."
    )
    max_length: int | None = Field(
        None, description="No more than this many characters."
    )
    answer_value_set: str | None = Field(
        None, description="Valueset containing permitted answers, as a canonical reference (uri)."
    )
    answer_option: list[QuestionnaireItemAnswerOptionInput] | None = Field(
        None, description="Permitted answer values."
    )
    initial: list[QuestionnaireItemInitialInput] | None = Field(
        None, description="Initial value(s) when item is first rendered."
    )
    item: list[QuestionnaireItemInput] | None = Field(
        None, description="Nested questions/groups beneath this one."
    )


QuestionnaireItemInput.model_rebuild()

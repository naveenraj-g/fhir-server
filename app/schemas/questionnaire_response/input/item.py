from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .answer import QuestionnaireResponseAnswerInput


class QuestionnaireResponseItemInput(BaseModel):
    """QuestionnaireResponse.item (0..*, recursive — item.item nests to
    unbounded depth, AND an item's own children may instead live under one
    of its answers' `item[]` — see
    app.models.questionnaire_response.core.QuestionnaireResponseModel's
    docstring for the full invariant). Mutually recursive with
    QuestionnaireResponseAnswerInput's own `item` field — both classes must
    call `model_rebuild()` after both are defined, done at the bottom of
    this module (see CLAUDE.md's Schema Conventions section)."""

    model_config = ConfigDict(extra="forbid")

    link_id: str = Field(
        ..., description="The linkId for the item this is answering, as defined in the matching Questionnaire."
    )
    definition: str | None = Field(
        None, description="ElementDefinition reference (uri) matching the linkId."
    )
    text: str | None = Field(None, description="Text that is displayed above the contents of the group or question.")
    answer: list[QuestionnaireResponseAnswerInput] | None = Field(
        None, description="The response(s) to this question."
    )
    item: list["QuestionnaireResponseItemInput"] | None = Field(
        None, description="Nested groups/questions beneath this one (mutually exclusive with populating answer.item on the same item — see the FHIR invariant 'Nested item can't be beneath both item and answer')."
    )


QuestionnaireResponseItemInput.model_rebuild()
QuestionnaireResponseAnswerInput.model_rebuild()

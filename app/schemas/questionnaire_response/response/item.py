from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .answer import FHIRQuestionnaireResponseAnswer, PlainQuestionnaireResponseAnswer

# ---------------------------------------------------------------------------
# FHIR (camelCase)
# ---------------------------------------------------------------------------


class FHIRQuestionnaireResponseItem(BaseModel):
    linkId: str
    definition: str | None = None
    text: str | None = None
    answer: list[FHIRQuestionnaireResponseAnswer] | None = None
    item: list[FHIRQuestionnaireResponseItem] | None = None


FHIRQuestionnaireResponseAnswer.model_rebuild()
FHIRQuestionnaireResponseItem.model_rebuild()


# ---------------------------------------------------------------------------
# Plain (snake_case)
# ---------------------------------------------------------------------------


class PlainQuestionnaireResponseItem(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal row ID.")
    link_id: str = Field(..., description="The linkId for the item this is answering.")
    definition: str | None = Field(None, description="ElementDefinition reference (uri) matching the linkId.")
    text: str | None = Field(None, description="Text displayed above the group or question.")
    answer: list[PlainQuestionnaireResponseAnswer] | None = Field(None, description="The response(s) to this question.")
    item: list[PlainQuestionnaireResponseItem] | None = Field(None, description="Nested groups/questions beneath this one.")


PlainQuestionnaireResponseAnswer.model_rebuild()
PlainQuestionnaireResponseItem.model_rebuild()

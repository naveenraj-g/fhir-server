from pydantic import BaseModel, ConfigDict, Field

from .codeable_concept import ConditionCodeableConceptInput
from .reference import ConditionStageAssessmentInput


class ConditionStageInput(BaseModel):
    """Condition.stage (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")
    summary: ConditionCodeableConceptInput | None = Field(
        None, description="Simple summary (clinical description) of the stage."
    )
    assessment: list[ConditionStageAssessmentInput] | None = Field(
        None, description="Formal record of assessment of the stage."
    )
    type: ConditionCodeableConceptInput | None = Field(
        None, description="Kind of staging."
    )

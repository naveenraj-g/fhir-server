from pydantic import BaseModel, ConfigDict, Field

from .codeable_concept import ConditionCodeableConceptInput
from .reference import ConditionEvidenceDetailInput


class ConditionEvidenceInput(BaseModel):
    """Condition.evidence (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")
    code: list[ConditionCodeableConceptInput] | None = Field(
        None, description="Manifestation/symptom evidence."
    )
    detail: list[ConditionEvidenceDetailInput] | None = Field(
        None, description="Supporting information found elsewhere."
    )

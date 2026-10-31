from pydantic import BaseModel, ConfigDict, Field

from app.schemas.episode_of_care.input.codeable_concept import (
    EpisodeOfCareCodeableConceptInput,
)


class EpisodeOfCareDiagnosisInput(BaseModel):
    """Input representation of a diagnosis entry for EpisodeOfCare."""

    model_config = ConfigDict(extra="forbid")

    condition: str = Field(..., description="Conditions/problems/diagnoses this episode of care is for (Reference(Condition)).")
    condition_display: str | None = Field(None, description="Display string for condition.")
    role: EpisodeOfCareCodeableConceptInput | None = Field(
        None, description="Role that this diagnosis has within the episode of care."
    )
    rank: int | None = Field(None, ge=1, description="Ranking of the diagnosis (for each role type).")

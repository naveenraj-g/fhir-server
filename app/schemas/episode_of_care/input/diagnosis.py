from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse
from app.schemas.episode_of_care.input.codeable_concept import (
    EpisodeOfCareCodeableConceptInput,
)


class EpisodeOfCareDiagnosisInput(BaseModel):
    """Input representation of a diagnosis entry for EpisodeOfCare."""

    model_config = ConfigDict(extra="forbid")

    condition: str | None = Field(
        None, description="Conditions/problems/diagnoses this episode of care is for (Reference(Condition))."
    )
    condition_display: str | None = Field(None, description="Display string for condition.")
    condition_identifier_use: IdentifierUse | None = Field(None, description="Condition identifier use.")
    condition_identifier_type_system: str | None = Field(None, description="Condition identifier type system.")
    condition_identifier_type_version: str | None = Field(None, description="Condition identifier type version.")
    condition_identifier_type_code: str | None = Field(None, description="Condition identifier type code.")
    condition_identifier_type_display: str | None = Field(None, description="Condition identifier type display.")
    condition_identifier_type_user_selected: bool | None = Field(
        None, description="Condition identifier type user selected."
    )
    condition_identifier_type_text: str | None = Field(None, description="Condition identifier type text.")
    condition_identifier_system: str | None = Field(None, description="Condition identifier system.")
    condition_identifier_value: str | None = Field(None, description="Condition identifier value.")
    condition_identifier_period_start: datetime | None = Field(
        None, description="Condition identifier period start."
    )
    condition_identifier_period_end: datetime | None = Field(
        None, description="Condition identifier period end."
    )
    role: EpisodeOfCareCodeableConceptInput | None = Field(
        None, description="Role that this diagnosis has within the episode of care."
    )
    rank: int | None = Field(None, ge=1, description="Ranking of the diagnosis (for each role type).")

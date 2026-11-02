from pydantic import BaseModel, ConfigDict, Field


class ImmunizationRecommendationCodingInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    system: str | None = Field(None, description="Identity of the terminology system.")
    version: str | None = Field(None, description="Version of the system.")
    code: str | None = Field(None, description="Symbol in syntax defined by the system.")
    display: str | None = Field(None, description="Representation defined by the system.")
    user_selected: bool | None = Field(None, description="If this coding was chosen directly by the user.")


class ImmunizationRecommendationCodeableConceptInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    coding: list[ImmunizationRecommendationCodingInput] | None = Field(
        None, description="Code defined by a terminology system."
    )
    text: str | None = Field(None, description="Plain text representation of the concept.")

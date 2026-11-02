from pydantic import BaseModel, ConfigDict, Field


class PlainImmunizationRecommendationCoding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = Field(None, description="Internal DB ID of coding row.")
    system: str | None = Field(None, description="Identity of the terminology system.")
    version: str | None = Field(None, description="Version of the system.")
    code: str | None = Field(None, description="Symbol in syntax defined by the system.")
    display: str | None = Field(None, description="Representation defined by the system.")
    user_selected: bool | None = Field(None, description="If this coding was chosen directly by the user.")


class PlainImmunizationRecommendationCodeableConcept(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = Field(None, description="Internal DB ID of parent child row if applicable.")
    coding: list[PlainImmunizationRecommendationCoding] | None = Field(
        None, description="Code defined by a terminology system."
    )
    text: str | None = Field(None, description="Plain text representation of the concept.")

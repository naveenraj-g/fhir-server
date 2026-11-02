from pydantic import BaseModel, ConfigDict, Field

from app.schemas.immunization.input.codeable_concept import (
    ImmunizationCodeableConceptInput,
)
from app.schemas.immunization.input.reference import ImmunizationActorInput


class ImmunizationPerformerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    function: ImmunizationCodeableConceptInput | None = Field(
        None, description="What the performer did."
    )
    actor: ImmunizationActorInput = Field(
        ..., description="Individual or organization who was performing."
    )

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.immunization.input.reference import (
    ImmunizationReactionDetailInput,
)


class ImmunizationReactionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: datetime | None = Field(None, description="When reaction started.")
    detail: ImmunizationReactionDetailInput | None = Field(
        None, description="Additional information on reaction (Reference(Observation))."
    )
    reported: bool | None = Field(None, description="Indicates self-reported reaction.")

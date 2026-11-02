from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRReference
from app.schemas.immunization.response.reference import (
    PlainImmunizationReference,
)


class FHIRImmunizationReaction(BaseModel):
    model_config = ConfigDict(extra="allow")

    date: str | None = Field(None, description="When reaction started.")
    detail: FHIRReference | None = Field(None, description="Additional information on reaction.")
    reported: bool | None = Field(None, description="Indicates self-reported reaction.")


class PlainImmunizationReaction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID.")
    date: datetime | None = Field(None, description="When reaction started.")
    detail: PlainImmunizationReference | None = Field(None, description="Additional information on reaction.")
    reported: bool | None = Field(None, description="Indicates self-reported reaction.")

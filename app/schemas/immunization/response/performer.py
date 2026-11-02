from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRCodeableConcept, FHIRReference
from app.schemas.immunization.response.codeable_concept import (
    PlainImmunizationCodeableConcept,
)
from app.schemas.immunization.response.reference import (
    PlainImmunizationReference,
)


class FHIRImmunizationPerformer(BaseModel):
    model_config = ConfigDict(extra="allow")

    function: FHIRCodeableConcept | None = Field(None, description="What the performer did.")
    actor: FHIRReference = Field(..., description="Individual or organization who was performing.")


class PlainImmunizationPerformer(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID.")
    function: PlainImmunizationCodeableConcept | None = Field(None, description="What the performer did.")
    actor: PlainImmunizationReference = Field(..., description="Individual or organization who was performing.")

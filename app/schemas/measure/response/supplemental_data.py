from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRCodeableConcept
from app.schemas.measure.response.codeable_concept import (
    PlainMeasureConcept,
    PlainMeasureSingleConcept,
)
from app.schemas.measure.response.group import (
    FHIRExpression,
    PlainMeasureExpression,
)


class FHIRMeasureSupplementalData(BaseModel):
    """FHIR R4 Measure.supplementalData."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    code: FHIRCodeableConcept | None = None
    usage: list[FHIRCodeableConcept] | None = None
    description: str | None = None
    criteria: FHIRExpression = Field(..., description="Criteria for supplemental data.")


class PlainMeasureSupplementalData(BaseModel):
    """Plain representation of Measure supplementalData."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    code: PlainMeasureSingleConcept | None = None
    usage: list[PlainMeasureConcept] | None = None
    description: str | None = None
    criteria: PlainMeasureExpression | None = None

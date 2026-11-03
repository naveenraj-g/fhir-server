from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRCodeableConcept
from app.schemas.measure.response.codeable_concept import PlainMeasureSingleConcept


class FHIRExpression(BaseModel):
    """FHIR R4 Expression representation."""

    model_config = ConfigDict(extra="allow")

    description: str | None = None
    name: str | None = None
    language: str = Field(..., description="Language of expression.")
    expression: str | None = None
    reference: str | None = None


class PlainMeasureExpression(BaseModel):
    """Plain representation of Expression."""

    model_config = ConfigDict(extra="allow")

    description: str | None = None
    name: str | None = None
    language: str | None = None
    expression: str | None = None
    reference: str | None = None


class FHIRMeasureGroupPopulation(BaseModel):
    """FHIR R4 Measure.group.population."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    code: FHIRCodeableConcept | None = None
    description: str | None = None
    criteria: FHIRExpression = Field(..., description="Criteria for population.")


class PlainMeasureGroupPopulation(BaseModel):
    """Plain representation of Measure group population."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    code: PlainMeasureSingleConcept | None = None
    description: str | None = None
    criteria: PlainMeasureExpression | None = None


class FHIRMeasureGroupStratifierComponent(BaseModel):
    """FHIR R4 Measure.group.stratifier.component."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    code: FHIRCodeableConcept | None = None
    description: str | None = None
    criteria: FHIRExpression = Field(..., description="Criteria for component.")


class PlainMeasureGroupStratifierComponent(BaseModel):
    """Plain representation of Measure group stratifier component."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    code: PlainMeasureSingleConcept | None = None
    description: str | None = None
    criteria: PlainMeasureExpression | None = None


class FHIRMeasureGroupStratifier(BaseModel):
    """FHIR R4 Measure.group.stratifier."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    code: FHIRCodeableConcept | None = None
    description: str | None = None
    criteria: FHIRExpression | None = None
    component: list[FHIRMeasureGroupStratifierComponent] | None = None


class PlainMeasureGroupStratifier(BaseModel):
    """Plain representation of Measure group stratifier."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    code: PlainMeasureSingleConcept | None = None
    description: str | None = None
    criteria: PlainMeasureExpression | None = None
    component: list[PlainMeasureGroupStratifierComponent] | None = None


class FHIRMeasureGroup(BaseModel):
    """FHIR R4 Measure.group."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    code: FHIRCodeableConcept | None = None
    description: str | None = None
    population: list[FHIRMeasureGroupPopulation] | None = None
    stratifier: list[FHIRMeasureGroupStratifier] | None = None


class PlainMeasureGroup(BaseModel):
    """Plain representation of Measure group."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    code: PlainMeasureSingleConcept | None = None
    description: str | None = None
    population: list[PlainMeasureGroupPopulation] | None = None
    stratifier: list[PlainMeasureGroupStratifier] | None = None

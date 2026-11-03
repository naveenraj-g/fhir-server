from pydantic import BaseModel, ConfigDict, Field

from app.schemas.measure.input.codeable_concept import MeasureCodeableConceptInput


class MeasureExpressionInput(BaseModel):
    """Expression input schema (FHIR R4)."""

    model_config = ConfigDict(extra="forbid")

    description: str | None = Field(None, description="Natural language description of the condition.")
    name: str | None = Field(None, description="Short name assigned to expression for reuse.")
    language: str = Field(..., description="text/cql | text/fhirpath | application/x-fhir-query | etc.")
    expression: str | None = Field(None, description="Expression in specified language.")
    reference: str | None = Field(None, description="Where the expression is found (uri).")


class MeasureGroupPopulationInput(BaseModel):
    """Measure.group.population input schema."""

    model_config = ConfigDict(extra="forbid")

    code: MeasureCodeableConceptInput | None = Field(
        None, description="initial-population | numerator | denominator | denominator-exclusion | etc."
    )
    description: str | None = Field(None, description="The human readable description of this population criteria.")
    criteria: MeasureExpressionInput = Field(..., description="The criteria that defines this population (1..1 Expression).")


class MeasureGroupStratifierComponentInput(BaseModel):
    """Measure.group.stratifier.component input schema."""

    model_config = ConfigDict(extra="forbid")

    code: MeasureCodeableConceptInput | None = Field(None, description="Meaning of the stratifier component.")
    description: str | None = Field(None, description="The human readable description of this stratifier component.")
    criteria: MeasureExpressionInput = Field(..., description="The criteria that defines this stratifier component (1..1 Expression).")


class MeasureGroupStratifierInput(BaseModel):
    """Measure.group.stratifier input schema."""

    model_config = ConfigDict(extra="forbid")

    code: MeasureCodeableConceptInput | None = Field(None, description="Meaning of the stratifier.")
    description: str | None = Field(None, description="The human readable description of this stratifier.")
    criteria: MeasureExpressionInput | None = Field(None, description="How the stratifier should be valued (0..1 Expression).")
    component: list[MeasureGroupStratifierComponentInput] | None = Field(
        None, description="Stratifier criteria component for composite stratifiers."
    )


class MeasureGroupInput(BaseModel):
    """Measure.group input schema."""

    model_config = ConfigDict(extra="forbid")

    code: MeasureCodeableConceptInput | None = Field(None, description="Meaning of the group.")
    description: str | None = Field(None, description="Summary description of group.")
    population: list[MeasureGroupPopulationInput] | None = Field(None, description="What populations are in the group.")
    stratifier: list[MeasureGroupStratifierInput] | None = Field(None, description="Stratifier criteria for the measure.")

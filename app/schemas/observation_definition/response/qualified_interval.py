from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRCodeableConcept, PlainCodingRow
from app.schemas.questionnaire.response import FHIRRange


class FHIRQualifiedInterval(BaseModel):
    """ObservationDefinition.qualifiedInterval FHIR representation."""

    model_config = ConfigDict(extra="allow")

    category: str | None = Field(None, description="reference | critical | absolute")
    range: FHIRRange | None = Field(None, description="The low and high values determining the interval.")
    context: FHIRCodeableConcept | None = Field(None, description="Health context the range applies to.")
    appliesTo: list[FHIRCodeableConcept] | None = Field(None, description="Target population this reference range applies to.")
    gender: str | None = Field(None, description="Sex of the population the range applies to.")
    age: FHIRRange | None = Field(None, description="Age at which this reference range is applicable.")
    gestationalAge: FHIRRange | None = Field(None, description="Gestational age in pregnancy.")
    condition: str | None = Field(None, description="Condition for which the reference range is valid.")


class PlainObservationDefinitionQualifiedIntervalAppliesTo(BaseModel):
    """One appliesTo entry on a plain qualified interval."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal DB ID.")
    text: str | None = Field(None, description="Applies to text.")
    codings: list[PlainCodingRow] | None = Field(None, description="Codings.")


class PlainObservationDefinitionQualifiedInterval(BaseModel):
    """Plain (snake_case) ObservationDefinition qualifiedInterval response."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal DB ID.")
    category: str | None = Field(None, description="reference | critical | absolute")
    range_low_value: float | None = Field(None, description="range.low value.")
    range_low_unit: str | None = Field(None, description="range.low unit.")
    range_low_system: str | None = Field(None, description="range.low system.")
    range_low_code: str | None = Field(None, description="range.low code.")
    range_high_value: float | None = Field(None, description="range.high value.")
    range_high_unit: str | None = Field(None, description="range.high unit.")
    range_high_system: str | None = Field(None, description="range.high system.")
    range_high_code: str | None = Field(None, description="range.high code.")

    context_text: str | None = Field(None, description="Context text.")
    context_codings: list[PlainCodingRow] | None = Field(None, description="Context codings.")
    applies_to: list[PlainObservationDefinitionQualifiedIntervalAppliesTo] | None = Field(
        None, description="Target populations."
    )
    gender: str | None = Field(None, description="male | female | other | unknown")

    age_low_value: float | None = Field(None, description="age.low value.")
    age_low_unit: str | None = Field(None, description="age.low unit.")
    age_low_system: str | None = Field(None, description="age.low system.")
    age_low_code: str | None = Field(None, description="age.low code.")
    age_high_value: float | None = Field(None, description="age.high value.")
    age_high_unit: str | None = Field(None, description="age.high unit.")
    age_high_system: str | None = Field(None, description="age.high system.")
    age_high_code: str | None = Field(None, description="age.high code.")

    gestational_age_low_value: float | None = Field(None, description="gestationalAge.low value.")
    gestational_age_low_unit: str | None = Field(None, description="gestationalAge.low unit.")
    gestational_age_low_system: str | None = Field(None, description="gestationalAge.low system.")
    gestational_age_low_code: str | None = Field(None, description="gestationalAge.low code.")
    gestational_age_high_value: float | None = Field(None, description="gestationalAge.high value.")
    gestational_age_high_unit: str | None = Field(None, description="gestationalAge.high unit.")
    gestational_age_high_system: str | None = Field(None, description="gestationalAge.high system.")
    gestational_age_high_code: str | None = Field(None, description="gestationalAge.high code.")

    condition: str | None = Field(None, description="Condition text.")

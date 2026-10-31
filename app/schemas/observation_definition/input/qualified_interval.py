from pydantic import BaseModel, ConfigDict, Field

from app.models.observation_definition.enums import (
    ObservationDefinitionGender,
    ObservationDefinitionQualifiedIntervalCategory,
)

from .codeable_concept import ObservationDefinitionCodeableConceptInput


class ObservationDefinitionQualifiedIntervalInput(BaseModel):
    """ObservationDefinition.qualifiedInterval (0..*) input schema."""

    model_config = ConfigDict(extra="forbid")

    category: ObservationDefinitionQualifiedIntervalCategory | None = Field(
        None, description="reference | critical | absolute"
    )
    range_low_value: float | None = Field(None, description="range.low value.")
    range_low_unit: str | None = Field(None, description="range.low unit.")
    range_low_system: str | None = Field(None, description="range.low system.")
    range_low_code: str | None = Field(None, description="range.low code.")
    range_high_value: float | None = Field(None, description="range.high value.")
    range_high_unit: str | None = Field(None, description="range.high unit.")
    range_high_system: str | None = Field(None, description="range.high system.")
    range_high_code: str | None = Field(None, description="range.high code.")

    context: ObservationDefinitionCodeableConceptInput | None = Field(
        None, description="Context code, e.g. normal or therapeutic."
    )
    applies_to: list[ObservationDefinitionCodeableConceptInput] | None = Field(
        None, description="Target population this reference range applies to."
    )
    gender: ObservationDefinitionGender | None = Field(
        None, description="male | female | other | unknown"
    )

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

    condition: str | None = Field(
        None, description="Condition for which the reference range is valid."
    )

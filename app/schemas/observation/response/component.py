from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow

from .codeable_concept import PlainObservationCodeableConcept
from .reference_range import PlainObservationReferenceRange


class PlainObservationComponent(BaseModel):
    """Observation.component (0..* — a real child-table row). `value[x]`
    reuses the identical 11-variant flattening shape as the root
    resource's own `value[x]` (see PlainObservationResponse)."""

    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal row ID.")

    code_codings: list[PlainCodingRow] | None = Field(None, description="Coding(s) for the component's type.")
    code_text: str | None = Field(None, description="A human language representation of the component's type.")

    value_quantity_value: float | None = Field(None, description="value[x]: Quantity — numeric value.")
    value_quantity_comparator: str | None = Field(None, description="value[x]: Quantity — comparator.")
    value_quantity_unit: str | None = Field(None, description="value[x]: Quantity — unit.")
    value_quantity_system: str | None = Field(None, description="value[x]: Quantity — unit system.")
    value_quantity_code: str | None = Field(None, description="value[x]: Quantity — coded unit form.")
    value_codeable_concept_codings: list[PlainCodingRow] | None = Field(None, description="value[x]: CodeableConcept — coding(s).")
    value_codeable_concept_text: str | None = Field(None, description="value[x]: CodeableConcept — text.")
    value_string: str | None = Field(None, description="value[x]: string.")
    value_boolean: bool | None = Field(None, description="value[x]: boolean.")
    value_integer: int | None = Field(None, description="value[x]: integer.")
    value_range_low_value: float | None = Field(None, description="value[x]: Range.low — numeric value.")
    value_range_low_unit: str | None = Field(None, description="value[x]: Range.low — unit.")
    value_range_low_system: str | None = Field(None, description="value[x]: Range.low — unit system.")
    value_range_low_code: str | None = Field(None, description="value[x]: Range.low — coded unit form.")
    value_range_high_value: float | None = Field(None, description="value[x]: Range.high — numeric value.")
    value_range_high_unit: str | None = Field(None, description="value[x]: Range.high — unit.")
    value_range_high_system: str | None = Field(None, description="value[x]: Range.high — unit system.")
    value_range_high_code: str | None = Field(None, description="value[x]: Range.high — coded unit form.")
    value_ratio_numerator_value: float | None = Field(None, description="value[x]: Ratio.numerator — numeric value.")
    value_ratio_numerator_comparator: str | None = Field(None, description="value[x]: Ratio.numerator — comparator.")
    value_ratio_numerator_unit: str | None = Field(None, description="value[x]: Ratio.numerator — unit.")
    value_ratio_numerator_system: str | None = Field(None, description="value[x]: Ratio.numerator — unit system.")
    value_ratio_numerator_code: str | None = Field(None, description="value[x]: Ratio.numerator — coded unit form.")
    value_ratio_denominator_value: float | None = Field(None, description="value[x]: Ratio.denominator — numeric value.")
    value_ratio_denominator_comparator: str | None = Field(None, description="value[x]: Ratio.denominator — comparator.")
    value_ratio_denominator_unit: str | None = Field(None, description="value[x]: Ratio.denominator — unit.")
    value_ratio_denominator_system: str | None = Field(None, description="value[x]: Ratio.denominator — unit system.")
    value_ratio_denominator_code: str | None = Field(None, description="value[x]: Ratio.denominator — coded unit form.")
    value_sampled_data_origin_value: float | None = Field(None, description="value[x]: SampledData.origin — numeric value.")
    value_sampled_data_origin_unit: str | None = Field(None, description="value[x]: SampledData.origin — unit.")
    value_sampled_data_origin_system: str | None = Field(None, description="value[x]: SampledData.origin — unit system.")
    value_sampled_data_origin_code: str | None = Field(None, description="value[x]: SampledData.origin — coded unit form.")
    value_sampled_data_period: float | None = Field(None, description="value[x]: SampledData.period.")
    value_sampled_data_factor: float | None = Field(None, description="value[x]: SampledData.factor.")
    value_sampled_data_lower_limit: float | None = Field(None, description="value[x]: SampledData.lowerLimit.")
    value_sampled_data_upper_limit: float | None = Field(None, description="value[x]: SampledData.upperLimit.")
    value_sampled_data_dimensions: int | None = Field(None, description="value[x]: SampledData.dimensions.")
    value_sampled_data_data: str | None = Field(None, description="value[x]: SampledData.data.")
    value_time: str | None = Field(None, description="value[x]: time.")
    value_date_time: str | None = Field(None, description="value[x]: dateTime.")
    value_period_start: str | None = Field(None, description="value[x]: Period — start.")
    value_period_end: str | None = Field(None, description="value[x]: Period — end.")

    data_absent_reason_codings: list[PlainCodingRow] | None = Field(None, description="Why the component result is missing — coding(s).")
    data_absent_reason_text: str | None = Field(None, description="Why the component result is missing — text.")
    interpretation: list[PlainObservationCodeableConcept] | None = Field(None, description="Categorical assessment of the component result.")
    reference_range: list[PlainObservationReferenceRange] | None = Field(None, description="Guidance for interpreting the component's value.")

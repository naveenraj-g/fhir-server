from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import ObservationQuantityComparator

from .codeable_concept import ObservationCodeableConceptInput
from .reference_range import ObservationReferenceRangeInput


class ObservationComponentInput(BaseModel):
    """Observation.component (0..*). `code` (1..1 CodeableConcept) and
    `dataAbsentReason` (0..1 CodeableConcept) are flattened with `_text`;
    `value[x]` reuses the identical 11-variant flattening shape as the
    root resource's own `value[x]` (see ObservationCreateSchema)."""

    model_config = ConfigDict(extra="forbid")

    code: ObservationCodeableConceptInput = Field(..., description="Type of component observation (code; LOINC codes).")

    value_quantity_value: float | None = Field(None, description="value[x]: Quantity — numeric value.")
    value_quantity_comparator: ObservationQuantityComparator | None = Field(None, description="value[x]: Quantity — comparator.")
    value_quantity_unit: str | None = Field(None, description="value[x]: Quantity — unit.")
    value_quantity_system: str | None = Field(None, description="value[x]: Quantity — unit system.")
    value_quantity_code: str | None = Field(None, description="value[x]: Quantity — coded unit form.")
    value_codeable_concept: ObservationCodeableConceptInput | None = Field(None, description="value[x]: CodeableConcept.")
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
    value_ratio_numerator_comparator: ObservationQuantityComparator | None = Field(None, description="value[x]: Ratio.numerator — comparator.")
    value_ratio_numerator_unit: str | None = Field(None, description="value[x]: Ratio.numerator — unit.")
    value_ratio_numerator_system: str | None = Field(None, description="value[x]: Ratio.numerator — unit system.")
    value_ratio_numerator_code: str | None = Field(None, description="value[x]: Ratio.numerator — coded unit form.")
    value_ratio_denominator_value: float | None = Field(None, description="value[x]: Ratio.denominator — numeric value.")
    value_ratio_denominator_comparator: ObservationQuantityComparator | None = Field(None, description="value[x]: Ratio.denominator — comparator.")
    value_ratio_denominator_unit: str | None = Field(None, description="value[x]: Ratio.denominator — unit.")
    value_ratio_denominator_system: str | None = Field(None, description="value[x]: Ratio.denominator — unit system.")
    value_ratio_denominator_code: str | None = Field(None, description="value[x]: Ratio.denominator — coded unit form.")
    value_sampled_data_origin_value: float | None = Field(None, description="value[x]: SampledData.origin — numeric value.")
    value_sampled_data_origin_unit: str | None = Field(None, description="value[x]: SampledData.origin — unit.")
    value_sampled_data_origin_system: str | None = Field(None, description="value[x]: SampledData.origin — unit system.")
    value_sampled_data_origin_code: str | None = Field(None, description="value[x]: SampledData.origin — coded unit form.")
    value_sampled_data_period: float | None = Field(None, description="value[x]: SampledData.period — ms between samples.")
    value_sampled_data_factor: float | None = Field(None, description="value[x]: SampledData.factor — correction factor.")
    value_sampled_data_lower_limit: float | None = Field(None, description="value[x]: SampledData.lowerLimit.")
    value_sampled_data_upper_limit: float | None = Field(None, description="value[x]: SampledData.upperLimit.")
    value_sampled_data_dimensions: int | None = Field(None, description="value[x]: SampledData.dimensions — sample points per time point.")
    value_sampled_data_data: str | None = Field(None, description="value[x]: SampledData.data — space-separated values.")
    value_time: time | None = Field(None, description="value[x]: time.")
    value_date_time: datetime | None = Field(None, description="value[x]: dateTime.")
    value_period_start: datetime | None = Field(None, description="value[x]: Period — start.")
    value_period_end: datetime | None = Field(None, description="value[x]: Period — end.")

    data_absent_reason: ObservationCodeableConceptInput | None = Field(None, description="Why the component result is missing.")
    interpretation: list[ObservationCodeableConceptInput] | None = Field(None, description="Categorical assessment of the component result.")
    reference_range: list[ObservationReferenceRangeInput] | None = Field(None, description="Guidance for interpreting the component's value.")

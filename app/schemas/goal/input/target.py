from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class GoalTargetInput(BaseModel):
    """Goal.target (0..*) BackboneElement input schema."""

    model_config = ConfigDict(extra="forbid")

    # measure (0..1 CodeableConcept)
    measure_coding: list[CodingInput] | None = Field(
        None, description="The parameter for which goals are being tracked (CodeableConcept.coding)."
    )
    measure_text: str | None = Field(
        None, description="The parameter for which goals are being tracked (CodeableConcept.text)."
    )

    # detail[x] (0..1 Quantity | Range | CodeableConcept | string | boolean | integer | Ratio)
    detail_string: str | None = Field(None, description="The target value to be achieved as string.")
    detail_boolean: bool | None = Field(None, description="The target value to be achieved as boolean.")
    detail_integer: int | None = Field(None, description="The target value to be achieved as integer.")

    detail_quantity_value: Decimal | float | None = Field(None, description="Target Quantity value.")
    detail_quantity_unit: str | None = Field(None, description="Target Quantity unit.")
    detail_quantity_system: str | None = Field(None, description="Target Quantity system.")
    detail_quantity_code: str | None = Field(None, description="Target Quantity code.")
    detail_quantity_comparator: str | None = Field(None, description="Target Quantity comparator (< | <= | >= | >).")

    detail_range_low_value: Decimal | float | None = Field(None, description="Target Range low value.")
    detail_range_low_unit: str | None = Field(None, description="Target Range low unit.")
    detail_range_low_system: str | None = Field(None, description="Target Range low system.")
    detail_range_low_code: str | None = Field(None, description="Target Range low code.")
    detail_range_high_value: Decimal | float | None = Field(None, description="Target Range high value.")
    detail_range_high_unit: str | None = Field(None, description="Target Range high unit.")
    detail_range_high_system: str | None = Field(None, description="Target Range high system.")
    detail_range_high_code: str | None = Field(None, description="Target Range high code.")

    detail_ratio_numerator_value: Decimal | float | None = Field(None, description="Target Ratio numerator value.")
    detail_ratio_numerator_unit: str | None = Field(None, description="Target Ratio numerator unit.")
    detail_ratio_numerator_system: str | None = Field(None, description="Target Ratio numerator system.")
    detail_ratio_numerator_code: str | None = Field(None, description="Target Ratio numerator code.")
    detail_ratio_denominator_value: Decimal | float | None = Field(None, description="Target Ratio denominator value.")
    detail_ratio_denominator_unit: str | None = Field(None, description="Target Ratio denominator unit.")
    detail_ratio_denominator_system: str | None = Field(None, description="Target Ratio denominator system.")
    detail_ratio_denominator_code: str | None = Field(None, description="Target Ratio denominator code.")

    detail_codeable_concept_coding: list[CodingInput] | None = Field(None, description="Target CodeableConcept coding.")
    detail_codeable_concept_text: str | None = Field(None, description="Target CodeableConcept text.")

    # due[x] (0..1 date | Duration)
    due_date: date | None = Field(None, description="Target reach date.")
    due_duration_value: Decimal | float | None = Field(None, description="Target reach duration value.")
    due_duration_unit: str | None = Field(None, description="Target reach duration unit.")
    due_duration_system: str | None = Field(None, description="Target reach duration system.")
    due_duration_code: str | None = Field(None, description="Target reach duration code.")

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    AuditFields,
    FHIRCodeableConcept,
    FHIRQuantity,
    FHIRRange,
    PlainCodingRow,
)


class FHIRGoalTarget(BaseModel):
    """FHIR R4 Goal.target backbone element."""

    model_config = ConfigDict(populate_by_name=True)

    measure: FHIRCodeableConcept | None = None
    detailQuantity: FHIRQuantity | None = None
    detailRange: FHIRRange | None = None
    detailCodeableConcept: FHIRCodeableConcept | None = None
    detailString: str | None = None
    detailBoolean: bool | None = None
    detailInteger: int | None = None
    detailRatio: dict | None = None
    dueDate: str | None = None
    dueDuration: FHIRQuantity | None = None


class PlainGoalTarget(AuditFields):
    """Plain snake_case serialization of a Goal target child row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="DB primary key of this target row.")
    measure_text: str | None = None
    measure_codings: list[PlainCodingRow] | None = None
    detail_string: str | None = None
    detail_boolean: bool | None = None
    detail_integer: int | None = None
    detail_quantity_value: float | None = None
    detail_quantity_unit: str | None = None
    detail_quantity_system: str | None = None
    detail_quantity_code: str | None = None
    detail_quantity_comparator: str | None = None
    detail_range_low_value: float | None = None
    detail_range_low_unit: str | None = None
    detail_range_low_system: str | None = None
    detail_range_low_code: str | None = None
    detail_range_high_value: float | None = None
    detail_range_high_unit: str | None = None
    detail_range_high_system: str | None = None
    detail_range_high_code: str | None = None
    detail_ratio_numerator_value: float | None = None
    detail_ratio_numerator_unit: str | None = None
    detail_ratio_numerator_system: str | None = None
    detail_ratio_numerator_code: str | None = None
    detail_ratio_denominator_value: float | None = None
    detail_ratio_denominator_unit: str | None = None
    detail_ratio_denominator_system: str | None = None
    detail_ratio_denominator_code: str | None = None
    detail_codeable_concept_text: str | None = None
    detail_codings: list[PlainCodingRow] | None = None
    due_date: str | None = None
    due_duration_value: float | None = None
    due_duration_unit: str | None = None
    due_duration_system: str | None = None
    due_duration_code: str | None = None

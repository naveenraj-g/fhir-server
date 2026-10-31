from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCoding,
    FHIRQuantity,
    FHIRRange,
    FHIRReference,
    PlainCodingRow,
)


class FHIRPlanDefinitionUseContext(BaseModel):
    """FHIR R4 UsageContext."""

    model_config = ConfigDict(extra="allow")

    code: FHIRCoding | None = None
    valueCodeableConcept: dict | None = None
    valueQuantity: FHIRQuantity | None = None
    valueRange: FHIRRange | None = None
    valueReference: FHIRReference | None = None


class PlainPlanDefinitionUseContext(BaseModel):
    """Plain UsageContext representation."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    code_system: str | None = None
    code_version: str | None = None
    code_code: str | None = None
    code_display: str | None = None
    code_user_selected: bool | None = None

    value_codeable_concept_text: str | None = None
    value_codeable_concept_codings: list[PlainCodingRow] | None = None

    value_quantity_value: float | None = None
    value_quantity_comparator: str | None = None
    value_quantity_unit: str | None = None
    value_quantity_system: str | None = None
    value_quantity_code: str | None = None

    value_range_low_value: float | None = None
    value_range_low_unit: str | None = None
    value_range_low_system: str | None = None
    value_range_low_code: str | None = None
    value_range_high_value: float | None = None
    value_range_high_unit: str | None = None
    value_range_high_system: str | None = None
    value_range_high_code: str | None = None

    value_reference: str | None = None
    value_reference_display: str | None = None

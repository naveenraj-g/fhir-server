from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRPeriod,
    FHIRQuantity,
    FHIRRange,
    FHIRReference,
)
from app.schemas.group.response.codeable_concept import PlainGroupCodeableConcept


class PlainGroupCharacteristic(BaseModel):
    """Plain response schema for Group characteristic."""

    model_config = ConfigDict(extra="ignore")

    id: int = Field(..., description="Internal DB ID.")
    code: PlainGroupCodeableConcept = Field(..., description="Kind of characteristic.")
    exclude: bool = Field(False, description="Group includes or excludes members with this characteristic.")
    period_start: datetime | None = Field(None, description="Period start.")
    period_end: datetime | None = Field(None, description="Period end.")
    value_boolean: bool | None = Field(None, description="Value (boolean).")
    value_codeable_concept: PlainGroupCodeableConcept | None = Field(None, description="Value (CodeableConcept).")
    value_quantity: dict[str, Any] | None = Field(None, description="Value (Quantity).")
    value_range: dict[str, Any] | None = Field(None, description="Value (Range).")
    value_reference: str | None = Field(None, description="Value (Reference).")
    value_reference_display: str | None = Field(None, description="Display text for reference.")


class FHIRGroupCharacteristic(BaseModel):
    """FHIR R4 Group characteristic element."""

    model_config = ConfigDict(extra="allow")

    code: FHIRCodeableConcept = Field(..., description="Kind of characteristic.")
    valueCodeableConcept: FHIRCodeableConcept | None = None
    valueBoolean: bool | None = None
    valueQuantity: FHIRQuantity | None = None
    valueRange: FHIRRange | None = None
    valueReference: FHIRReference | None = None
    exclude: bool = Field(False, description="Group includes or excludes members with this characteristic.")
    period: FHIRPeriod | None = None

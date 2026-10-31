from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.group.input.codeable_concept import GroupCodeableConceptInput


class GroupCharacteristicInput(BaseModel):
    """Include / Exclude group members by characteristic."""

    model_config = ConfigDict(extra="forbid")

    code: GroupCodeableConceptInput = Field(
        ..., description="Kind of characteristic."
    )
    exclude: bool = Field(
        False, description="Group includes or excludes members with this characteristic."
    )
    period_start: datetime | None = Field(
        None, description="Period over which characteristic is tested (start)."
    )
    period_end: datetime | None = Field(
        None, description="Period over which characteristic is tested (end)."
    )

    # Choice value[x]
    value_boolean: bool | None = Field(
        None, description="Value held by characteristic (boolean)."
    )
    value_codeable_concept: GroupCodeableConceptInput | None = Field(
        None, description="Value held by characteristic (CodeableConcept)."
    )
    value_quantity: dict[str, Any] | None = Field(
        None, description="Value held by characteristic (Quantity)."
    )
    value_range: dict[str, Any] | None = Field(
        None, description="Value held by characteristic (Range)."
    )
    value_reference: str | None = Field(
        None, description="Value held by characteristic (Reference string e.g. Location/230001)."
    )
    value_reference_display: str | None = Field(
        None, description="Display text for reference."
    )

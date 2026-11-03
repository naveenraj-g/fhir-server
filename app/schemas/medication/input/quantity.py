from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import MedicationQuantityComparator


class MedicationQuantityInput(BaseModel):
    """FHIR Quantity input."""

    model_config = ConfigDict(extra="forbid")

    value: float | None = Field(None, description="Numerical value (with implicit precision).")
    comparator: MedicationQuantityComparator | None = Field(None, description="< | <= | >= | > - how to understand the value.")
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(None, description="System that defines coded unit form.")
    code: str | None = Field(None, description="Coded form of the unit.")


class MedicationRatioInput(BaseModel):
    """FHIR Ratio input (numerator Quantity, denominator Quantity)."""

    model_config = ConfigDict(extra="forbid")

    numerator: MedicationQuantityInput | None = Field(None, description="Numerator value.")
    denominator: MedicationQuantityInput | None = Field(None, description="Denominator value.")

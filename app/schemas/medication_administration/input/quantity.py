from pydantic import BaseModel, ConfigDict, Field


class SimpleQuantityInput(BaseModel):
    """SimpleQuantity input (value, unit, system, code — no comparator)."""

    model_config = ConfigDict(extra="forbid")

    value: float | None = Field(None, description="Numerical value (with implicit precision).")
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(None, description="System that defines coded unit form.")
    code: str | None = Field(None, description="Coded form of the unit.")


class RatioInput(BaseModel):
    """Ratio input (numerator, denominator)."""

    model_config = ConfigDict(extra="forbid")

    numerator: SimpleQuantityInput | None = Field(None, description="Numerator value.")
    denominator: SimpleQuantityInput | None = Field(None, description="Denominator value.")

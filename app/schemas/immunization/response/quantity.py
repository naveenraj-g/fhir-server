from pydantic import BaseModel, ConfigDict, Field


class PlainSimpleQuantity(BaseModel):
    model_config = ConfigDict(extra="forbid")

    value: float | None = Field(None, description="Numerical value.")
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(None, description="System that defines coded unit form.")
    code: str | None = Field(None, description="Coded form of the unit.")

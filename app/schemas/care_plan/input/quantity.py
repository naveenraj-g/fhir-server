from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import CarePlanQuantityComparator


class CarePlanQuantityInput(BaseModel):
    """Quantity input for CarePlan (e.g. dailyAmount, quantity)."""

    model_config = ConfigDict(extra="forbid")
    value: float | None = Field(None, description="Numerical value (with implicit precision).")
    comparator: CarePlanQuantityComparator | None = Field(
        None, description="< | <= | >= | > - how to understand the value."
    )
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(None, description="System that defines coded unit form.")
    code: str | None = Field(None, description="Coded form of the unit.")

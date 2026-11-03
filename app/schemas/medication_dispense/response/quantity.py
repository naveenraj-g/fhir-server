from pydantic import BaseModel, ConfigDict


class PlainMedicationDispenseQuantity(BaseModel):
    model_config = ConfigDict(extra="allow")

    value: float | None = None
    unit: str | None = None
    system: str | None = None
    code: str | None = None

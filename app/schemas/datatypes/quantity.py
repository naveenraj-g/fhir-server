from pydantic import BaseModel


class FHIRQuantity(BaseModel):
    value: float | None = None
    comparator: str | None = None
    unit: str | None = None
    system: str | None = None
    code: str | None = None

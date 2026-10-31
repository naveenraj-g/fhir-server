from pydantic import BaseModel

from app.schemas.datatypes.quantity import FHIRQuantity


class FHIRRange(BaseModel):
    low: FHIRQuantity | None = None
    high: FHIRQuantity | None = None

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRQuantity


class FHIRRatio(BaseModel):
    model_config = ConfigDict(extra="allow")

    numerator: FHIRQuantity | None = None
    denominator: FHIRQuantity | None = None


class PlainMedicationQuantity(BaseModel):
    model_config = ConfigDict(extra="allow")

    value: float | None = None
    comparator: str | None = None
    unit: str | None = None
    system: str | None = None
    code: str | None = None


class PlainMedicationRatio(BaseModel):
    model_config = ConfigDict(extra="allow")

    numerator: PlainMedicationQuantity | None = None
    denominator: PlainMedicationQuantity | None = None

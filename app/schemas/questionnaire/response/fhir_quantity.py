"""FHIR R4 Quantity/Range — not in app.schemas.datatypes since Questionnaire
is the first resource in this codebase needing them as standalone types
(Encounter's own FHIRDuration, in app.schemas.encounter.response, is the
closest existing precedent for a Quantity-family type with no shared home)."""

from pydantic import BaseModel


class FHIRQuantity(BaseModel):
    value: float | None = None
    comparator: str | None = None
    unit: str | None = None
    system: str | None = None
    code: str | None = None


class FHIRRange(BaseModel):
    low: FHIRQuantity | None = None
    high: FHIRQuantity | None = None

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import MedicationKnowledgeQuantityComparator


class MedicationKnowledgeQuantityInput(BaseModel):
    """FHIR Quantity input."""

    model_config = ConfigDict(extra="forbid")

    value: float | None = Field(None, description="Numerical value (with implicit precision).")
    comparator: MedicationKnowledgeQuantityComparator | None = Field(None, description="< | <= | >= | > - how to understand the value.")
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(None, description="System that defines coded unit form.")
    code: str | None = Field(None, description="Coded form of the unit.")


class MedicationKnowledgeRatioInput(BaseModel):
    """FHIR Ratio input (numerator Quantity, denominator Quantity)."""

    model_config = ConfigDict(extra="forbid")

    numerator: MedicationKnowledgeQuantityInput | None = Field(None, description="Numerator value.")
    denominator: MedicationKnowledgeQuantityInput | None = Field(None, description="Denominator value.")


class MedicationKnowledgeMoneyInput(BaseModel):
    """FHIR Money input."""

    model_config = ConfigDict(extra="forbid")

    value: float | None = Field(None, description="Numerical value (with implicit precision).")
    currency: str | None = Field(None, description="ISO 4217 Currency Code.")

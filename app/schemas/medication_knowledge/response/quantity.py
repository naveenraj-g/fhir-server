from pydantic import BaseModel, ConfigDict


class MedicationKnowledgeQuantityResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    value: float | None = None
    comparator: str | None = None
    unit: str | None = None
    system: str | None = None
    code: str | None = None


class MedicationKnowledgeRatioResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    numerator: MedicationKnowledgeQuantityResponse | None = None
    denominator: MedicationKnowledgeQuantityResponse | None = None


class MedicationKnowledgeMoneyResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    value: float | None = None
    currency: str | None = None

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.medication_knowledge.input.codeable_concept import (
    MedicationKnowledgeCodeableConceptInput,
)
from app.schemas.medication_knowledge.input.quantity import (
    MedicationKnowledgeMoneyInput,
)


class MedicationKnowledgeCostInput(BaseModel):
    """MedicationKnowledge.cost (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    type: MedicationKnowledgeCodeableConceptInput = Field(
        ..., description="The category of the cost information."
    )
    source: str | None = Field(None, description="The source or owner for the price information.")
    cost: MedicationKnowledgeMoneyInput = Field(
        ..., description="The price of the medication."
    )

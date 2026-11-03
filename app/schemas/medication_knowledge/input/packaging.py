from pydantic import BaseModel, ConfigDict, Field

from app.schemas.medication_knowledge.input.codeable_concept import (
    MedicationKnowledgeCodeableConceptInput,
)
from app.schemas.medication_knowledge.input.quantity import (
    MedicationKnowledgeQuantityInput,
)


class MedicationKnowledgePackagingInput(BaseModel):
    """MedicationKnowledge.packaging (0..1 BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    type: MedicationKnowledgeCodeableConceptInput | None = Field(
        None, description="A code that defines the specific type of packaging."
    )
    quantity: MedicationKnowledgeQuantityInput | None = Field(
        None, description="The number of product units the package would contain."
    )

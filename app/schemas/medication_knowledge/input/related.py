from pydantic import BaseModel, ConfigDict, Field

from app.schemas.medication_knowledge.input.codeable_concept import (
    MedicationKnowledgeCodeableConceptInput,
)


class MedicationKnowledgeRelatedInput(BaseModel):
    """MedicationKnowledge.relatedMedicationKnowledge (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    type: MedicationKnowledgeCodeableConceptInput = Field(
        ..., description="Category of related medication knowledge."
    )
    reference: list[str] = Field(
        ...,
        description="Associated documentation or knowledge. Reference(MedicationKnowledge), e.g. ['MedicationKnowledge/600001'].",
    )

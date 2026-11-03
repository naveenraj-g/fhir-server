from pydantic import BaseModel, ConfigDict, Field

from app.schemas.medication_knowledge.input.codeable_concept import (
    MedicationKnowledgeCodeableConceptInput,
)


class MedicationKnowledgeMedicineClassificationInput(BaseModel):
    """MedicationKnowledge.medicineClassification (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    type: MedicationKnowledgeCodeableConceptInput = Field(
        ..., description="The type of category for the medication (for example, therapeutic classification, therapeutic sub-classification)."
    )
    classification: list[MedicationKnowledgeCodeableConceptInput] | None = Field(
        None, description="Specific category assigned to the medication."
    )

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.medication_knowledge.input.codeable_concept import (
    MedicationKnowledgeCodeableConceptInput,
)
from app.schemas.medication_knowledge.input.quantity import (
    MedicationKnowledgeQuantityInput,
)


class MedicationKnowledgeDrugCharacteristicInput(BaseModel):
    """MedicationKnowledge.drugCharacteristic (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    type: MedicationKnowledgeCodeableConceptInput | None = Field(
        None, description="Code specifying the type of characteristic of medicinal product."
    )
    value_codeable_concept: MedicationKnowledgeCodeableConceptInput | None = Field(
        None, description="Description of the characteristic as a CodeableConcept."
    )
    value_string: str | None = Field(
        None, description="Description of the characteristic as a string."
    )
    value_quantity: MedicationKnowledgeQuantityInput | None = Field(
        None, description="Description of the characteristic as a quantity."
    )
    value_base64_binary: str | None = Field(
        None, description="Description of the characteristic as a base64 string."
    )

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.medication_knowledge.input.quantity import (
    MedicationKnowledgeQuantityInput,
)


class MedicationKnowledgeKineticsInput(BaseModel):
    """MedicationKnowledge.kinetics (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    area_under_curve: list[MedicationKnowledgeQuantityInput] | None = Field(
        None, description="The drug concentration over time."
    )
    lethal_dose_50: list[MedicationKnowledgeQuantityInput] | None = Field(
        None, description="The median lethal dose of a drug."
    )
    half_life_period: MedicationKnowledgeQuantityInput | None = Field(
        None, description="The time required for half the quantity of drug to be eliminated."
    )

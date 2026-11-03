from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse
from app.schemas.medication_knowledge.input.codeable_concept import (
    MedicationKnowledgeCodeableConceptInput,
)
from app.schemas.medication_knowledge.input.quantity import (
    MedicationKnowledgeRatioInput,
)


class MedicationKnowledgeIngredientInput(BaseModel):
    """MedicationKnowledge.ingredient (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    item_codeable_concept: MedicationKnowledgeCodeableConceptInput | None = Field(
        None, description="Active or inactive ingredient code."
    )
    item_reference: str | None = Field(
        None,
        description="Active or inactive ingredient reference. Reference(Substance | Medication).",
    )
    item_display: str | None = Field(None, description="Display text for item reference.")
    item_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — purpose.")
    item_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    item_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    item_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    item_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    item_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user selected.")
    item_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    item_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    item_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    item_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — period start.")
    item_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — period end.")

    is_active: bool | None = Field(
        None, description="Active ingredient indicator."
    )
    strength: MedicationKnowledgeRatioInput | None = Field(
        None, description="Quantity of ingredient present."
    )

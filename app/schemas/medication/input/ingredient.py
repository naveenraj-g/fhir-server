from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse
from app.schemas.medication.input.codeable_concept import (
    MedicationCodeableConceptInput,
)
from app.schemas.medication.input.quantity import MedicationRatioInput


class MedicationIngredientInput(BaseModel):
    """Medication.ingredient (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    # item[x] (1..1 choice: CodeableConcept | Reference(Substance | Medication))
    item_codeable_concept: MedicationCodeableConceptInput | None = Field(
        None, description="The business code that represents the active or inactive ingredient."
    )
    item_reference: str | None = Field(
        None,
        description="The actual ingredient. Reference(Substance | Medication), e.g. 'Medication/250001'.",
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
    strength: MedicationRatioInput | None = Field(
        None, description="Quantity of ingredient present."
    )

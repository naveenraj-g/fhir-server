from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse
from app.schemas.medication_dispense.input.codeable_concept import (
    MedicationDispenseCodeableConceptInput,
)


class MedicationDispensePerformerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    function: MedicationDispenseCodeableConceptInput | None = Field(
        None, description="Type of performer."
    )
    actor: str = Field(
        ...,
        description="Individual who was performing. Reference(Practitioner | PractitionerRole | Organization | Patient | Device | RelatedPerson), e.g. 'Practitioner/30001'.",
    )
    actor_display: str | None = Field(None, description="Display text for actor.")
    actor_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — its purpose, if known.")
    actor_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    actor_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    actor_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    actor_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    actor_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether chosen directly by user.")
    actor_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    actor_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    actor_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    actor_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    actor_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")

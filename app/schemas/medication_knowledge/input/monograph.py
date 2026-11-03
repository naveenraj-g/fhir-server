from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse
from app.schemas.medication_knowledge.input.codeable_concept import (
    MedicationKnowledgeCodeableConceptInput,
)


class MedicationKnowledgeMonographInput(BaseModel):
    """MedicationKnowledge.monograph (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    type: MedicationKnowledgeCodeableConceptInput | None = Field(
        None, description="The category of monograph."
    )
    source: str | None = Field(
        None,
        description="Associated documentation about the medication. Reference(DocumentReference | Media).",
    )
    source_display: str | None = Field(None, description="Display text for source reference.")
    source_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — purpose.")
    source_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    source_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    source_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    source_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    source_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user selected.")
    source_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    source_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    source_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    source_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — period start.")
    source_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — period end.")

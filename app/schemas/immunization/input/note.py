from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class ImmunizationNoteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., description="The annotation  — text content (as markdown).")
    time: datetime | None = Field(None, description="When the annotation was made.")
    author_string: str | None = Field(None, description="Individual responsible for the annotation as a string.")
    author_reference: str | None = Field(None, description="FHIR reference string for author, e.g. 'Practitioner/30001'.")
    author_display: str | None = Field(None, description="Plain text display text for author.")

    # author.identifier fallback (11 columns)
    author_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — its purpose, if known.")
    author_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    author_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    author_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    author_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    author_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether chosen directly by user.")
    author_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    author_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    author_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    author_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    author_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")

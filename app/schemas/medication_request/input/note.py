from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class MedicationRequestNoteInput(BaseModel):
    """MedicationRequest.note (0..* Annotation). Mirrors
    app.schemas.service_request.input.note.ServiceRequestNoteInput."""

    model_config = ConfigDict(extra="forbid")
    author_string: str | None = Field(None, description="author[x]: string — free-text author.")
    author_reference: str | None = Field(None, description="author[x]: Reference — FHIR reference string.")
    author_reference_display: str | None = Field(None, description="author[x]: Reference — plain text display.")
    author_identifier_use: IdentifierUse | None = Field(
        None, description="Fallback identifier — identifies its purpose, if known."
    )
    author_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — code system for its type."
    )
    author_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type code system."
    )
    author_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — a symbol for its type."
    )
    author_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    author_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — whether its type was user-selected."
    )
    author_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    author_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    author_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    author_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    author_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of validity period."
    )
    time: datetime | None = Field(None, description="When this comment/annotation was made.")
    text: str = Field(..., description="The annotation text (markdown).")

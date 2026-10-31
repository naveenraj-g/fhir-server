from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class SpecimenNoteInput(BaseModel):
    """Specimen.note (0..* Annotation)."""

    model_config = ConfigDict(extra="forbid")
    author_string: str | None = Field(
        None, description="Individual responsible for the annotation (as a string)."
    )
    author_reference: str | None = Field(
        None, description="Individual responsible for the annotation (as a reference)."
    )
    author_display: str | None = Field(
        None, description="Plain text narrative identifying the author."
    )
    author_identifier_use: IdentifierUse | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    author_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    author_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    author_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    time: datetime | None = Field(
        None, description="When the annotation was made."
    )
    text: str = Field(
        ..., description="The annotation content (markdown text)."
    )

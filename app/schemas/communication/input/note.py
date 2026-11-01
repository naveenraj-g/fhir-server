from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class CommunicationNoteInput(BaseModel):
    """Communication.note (0..*) Annotation input."""

    model_config = ConfigDict(extra="forbid")

    author_string: str | None = Field(
        None, description="Individual responsible for the annotation as a plain string."
    )
    author_reference: str | None = Field(
        None, description="Individual responsible for the annotation as a FHIR reference."
    )
    author_display: str | None = Field(
        None, description="Display narrative for author reference."
    )
    author_identifier_use: IdentifierUse | None = Field(
        None, description="Fallback identifier purpose/use."
    )
    author_identifier_type_system: str | None = Field(
        None, description="Fallback identifier type system."
    )
    author_identifier_type_version: str | None = Field(
        None, description="Fallback identifier type version."
    )
    author_identifier_type_code: str | None = Field(
        None, description="Fallback identifier type code."
    )
    author_identifier_type_display: str | None = Field(
        None, description="Fallback identifier type display."
    )
    author_identifier_type_text: str | None = Field(
        None, description="Fallback identifier type text."
    )
    author_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier type user selected."
    )
    author_identifier_system: str | None = Field(
        None, description="Fallback identifier namespace system."
    )
    author_identifier_value: str | None = Field(
        None, description="Fallback identifier value."
    )
    author_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier period start."
    )
    author_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier period end."
    )
    time: datetime | None = Field(
        None, description="When the annotation was made."
    )
    text: str = Field(
        ..., description="The annotation text content."
    )

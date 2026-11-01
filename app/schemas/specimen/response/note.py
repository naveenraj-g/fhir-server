from pydantic import BaseModel, ConfigDict, Field


class PlainSpecimenNote(BaseModel):
    """Plain response shape for Specimen.note (0..* Annotation)."""

    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal DB ID.")
    author_string: str | None = Field(None, description="author[x]: string.")
    author_reference: str | None = Field(None, description="author[x]: Reference string.")
    author_id: int | None = Field(None, description="author[x]: Reference public ID.")
    author_type: str | None = Field(None, description="author[x]: Reference resource type.")
    author_display: str | None = Field(None, description="author[x]: Reference display.")
    author_identifier_use: str | None = None
    author_identifier_type_system: str | None = None
    author_identifier_type_version: str | None = None
    author_identifier_type_code: str | None = None
    author_identifier_type_display: str | None = None
    author_identifier_type_user_selected: bool | None = None
    author_identifier_type_text: str | None = None
    author_identifier_system: str | None = None
    author_identifier_value: str | None = None
    author_identifier_period_start: str | None = None
    author_identifier_period_end: str | None = None
    time: str | None = Field(None, description="When annotation was made.")
    text: str = Field(..., description="Annotation text.")

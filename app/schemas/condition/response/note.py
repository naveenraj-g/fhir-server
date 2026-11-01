from pydantic import BaseModel, ConfigDict, Field


class PlainConditionNote(BaseModel):
    """Plain response shape for Condition.note (0..* Annotation)."""

    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal DB ID.")
    author_string: str | None = Field(None, description="author[x]: string.")
    author_reference: str | None = Field(None, description="author[x]: Reference string.")
    author_id: int | None = Field(None, description="author[x]: Reference public ID.")
    author_type: str | None = Field(None, description="author[x]: Reference resource type.")
    author_display: str | None = Field(None, description="author[x]: Reference display.")
    author_identifier_use: str | None = Field(None, description="Fallback identifier — use.")
    author_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    author_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    author_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    author_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    author_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user_selected.")
    author_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    author_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    author_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    author_identifier_period_start: str | None = Field(None, description="Fallback identifier — period start.")
    author_identifier_period_end: str | None = Field(None, description="Fallback identifier — period end.")
    time: str | None = Field(None, description="When annotation was made.")
    text: str = Field(..., description="Annotation text.")

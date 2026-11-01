from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlainAllergyIntoleranceNote(BaseModel):
    """Plain representation of AllergyIntoleranceNote child row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    text: str = Field(..., description="The annotation content as text.")
    time: datetime | None = None
    author_string: str | None = None
    author_reference: str | None = None
    author_reference_type: str | None = None
    author_reference_id: int | None = None
    author_reference_display: str | None = None
    author_reference_identifier_use: str | None = Field(None, description="Fallback identifier — use.")
    author_reference_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    author_reference_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    author_reference_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    author_reference_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    author_reference_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user_selected.")
    author_reference_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    author_reference_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    author_reference_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    author_reference_identifier_period_start: str | None = Field(None, description="Fallback identifier — period start.")
    author_reference_identifier_period_end: str | None = Field(None, description="Fallback identifier — period end.")

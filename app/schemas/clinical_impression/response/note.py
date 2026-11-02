from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class PlainClinicalImpressionNote(BaseModel):
    """Plain snake_case representation for ClinicalImpression.note."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID.")
    author_string: str | None = Field(None, description="Author as plain text.")
    author_reference: str | None = Field(None, description="Author reference string.")
    author_type: str | None = Field(None, description="Author target resource type.")
    author_id: int | None = Field(None, description="Author target sequence ID.")
    author_display: str | None = Field(None, description="Author display text.")

    author_identifier_use: IdentifierUse | None = Field(None, description="Fallback author identifier use.")
    author_identifier_type_system: str | None = Field(None, description="Fallback author identifier type system.")
    author_identifier_type_version: str | None = Field(None, description="Fallback author identifier type version.")
    author_identifier_type_code: str | None = Field(None, description="Fallback author identifier type code.")
    author_identifier_type_display: str | None = Field(None, description="Fallback author identifier type display.")
    author_identifier_type_user_selected: bool | None = Field(None, description="Fallback author identifier type user selected.")
    author_identifier_type_text: str | None = Field(None, description="Fallback author identifier type text.")
    author_identifier_system: str | None = Field(None, description="Fallback author identifier system.")
    author_identifier_value: str | None = Field(None, description="Fallback author identifier value.")
    author_identifier_period_start: datetime | None = Field(None, description="Fallback author identifier period start.")
    author_identifier_period_end: datetime | None = Field(None, description="Fallback author identifier period end.")

    time: datetime | None = Field(None, description="When annotation was made.")
    text: str = Field(..., description="Note text.")


class ClinicalImpressionNoteListItem(PlainClinicalImpressionNote):
    """Sub-resource list item for note."""


class ClinicalImpressionNoteListResponse(BaseModel):
    """Sub-resource list response for notes."""

    model_config = ConfigDict(extra="forbid")

    data: list[ClinicalImpressionNoteListItem] = Field(..., description="List of notes.")
    total: int = Field(..., description="Total count.")

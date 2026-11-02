from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class PlainRiskAssessmentNote(BaseModel):
    """Plain snake_case RiskAssessment.note element."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID.")
    text: str = Field(..., description="The annotation text content (as markdown).")
    time: datetime | None = Field(None, description="When the annotation was made.")
    author_string: str | None = Field(None, description="Individual responsible for the annotation as a string.")
    author_reference: str | None = Field(None, description="FHIR reference string for author.")
    author_display: str | None = Field(None, description="Plain text display text for author.")

    # author.identifier fallback (11 columns)
    author_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier purpose.")
    author_identifier_type_system: str | None = Field(None, description="Fallback identifier type system.")
    author_identifier_type_version: str | None = Field(None, description="Fallback identifier type version.")
    author_identifier_type_code: str | None = Field(None, description="Fallback identifier type code.")
    author_identifier_type_display: str | None = Field(None, description="Fallback identifier type display.")
    author_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier user selected.")
    author_identifier_type_text: str | None = Field(None, description="Fallback identifier type text.")
    author_identifier_system: str | None = Field(None, description="Fallback identifier system.")
    author_identifier_value: str | None = Field(None, description="Fallback identifier value.")
    author_identifier_period_start: datetime | None = Field(None, description="Fallback identifier period start.")
    author_identifier_period_end: datetime | None = Field(None, description="Fallback identifier period end.")


class RiskAssessmentNoteListItem(PlainRiskAssessmentNote):
    """Sub-resource list item for RiskAssessment note."""


class RiskAssessmentNoteListResponse(BaseModel):
    """Sub-resource list response for RiskAssessment notes."""

    model_config = ConfigDict(extra="forbid")

    data: list[RiskAssessmentNoteListItem] = Field(..., description="List of notes.")
    total: int = Field(..., description="Total count of notes.")

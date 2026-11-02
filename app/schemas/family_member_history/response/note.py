from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlainFamilyMemberHistoryNote(BaseModel):
    """Plain snake_case shape for FamilyMemberHistory.note."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = Field(None, description="Internal database ID.")
    author_string: str | None = None
    author_reference: str | None = None
    author_reference_display: str | None = None
    author_identifier_use: str | None = None
    author_identifier_type_system: str | None = None
    author_identifier_type_version: str | None = None
    author_identifier_type_code: str | None = None
    author_identifier_type_display: str | None = None
    author_identifier_type_user_selected: bool | None = None
    author_identifier_type_text: str | None = None
    author_identifier_system: str | None = None
    author_identifier_value: str | None = None
    author_identifier_period_start: datetime | None = None
    author_identifier_period_end: datetime | None = None
    time: datetime | None = None
    text: str | None = None

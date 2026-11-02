from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlainFamilyMemberHistoryReasonReference(BaseModel):
    """Plain snake_case shape for FamilyMemberHistory.reasonReference."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = Field(None, description="Internal database ID.")
    reference: str | None = None
    display: str | None = None
    identifier_use: str | None = None
    identifier_type_system: str | None = None
    identifier_type_version: str | None = None
    identifier_type_code: str | None = None
    identifier_type_display: str | None = None
    identifier_type_user_selected: bool | None = None
    identifier_type_text: str | None = None
    identifier_system: str | None = None
    identifier_value: str | None = None
    identifier_period_start: datetime | None = None
    identifier_period_end: datetime | None = None

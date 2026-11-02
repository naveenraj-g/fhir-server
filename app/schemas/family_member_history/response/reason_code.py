from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow


class PlainFamilyMemberHistoryReasonCode(BaseModel):
    """Plain snake_case shape for FamilyMemberHistory.reasonCode."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = Field(None, description="Internal database ID.")
    coding: list[PlainCodingRow] | None = None
    text: str | None = None

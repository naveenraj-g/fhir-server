from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class PlainImmunizationEvaluationReference(BaseModel):
    """Plain snake_case Reference response."""

    model_config = ConfigDict(extra="forbid")

    reference: str | None = Field(None, description="FHIR reference string.")
    display: str | None = Field(None, description="Plain text display.")
    identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier use.")
    identifier_type_system: str | None = Field(None, description="Fallback identifier type system.")
    identifier_type_version: str | None = Field(None, description="Fallback identifier type version.")
    identifier_type_code: str | None = Field(None, description="Fallback identifier type code.")
    identifier_type_display: str | None = Field(None, description="Fallback identifier type display.")
    identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier type user selected.")
    identifier_type_text: str | None = Field(None, description="Fallback identifier type text.")
    identifier_system: str | None = Field(None, description="Fallback identifier system.")
    identifier_value: str | None = Field(None, description="Fallback identifier value.")
    identifier_period_start: datetime | None = Field(None, description="Fallback identifier period start.")
    identifier_period_end: datetime | None = Field(None, description="Fallback identifier period end.")

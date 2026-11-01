from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainIdentifierType
from app.schemas.enums import IdentifierUse


class PlainAllergyIntoleranceIdentifier(BaseModel):
    """Plain representation of AllergyIntoleranceIdentifier child row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    use: IdentifierUse | None = None
    type: PlainIdentifierType | None = None
    system: str | None = None
    value: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    assigner: str | None = None
    assigner_display: str | None = None
    assigner_identifier_use: str | None = Field(None, description="Fallback identifier — use.")
    assigner_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    assigner_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    assigner_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    assigner_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    assigner_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user_selected.")
    assigner_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    assigner_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    assigner_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    assigner_identifier_period_start: str | None = Field(None, description="Fallback identifier — period start.")
    assigner_identifier_period_end: str | None = Field(None, description="Fallback identifier — period end.")

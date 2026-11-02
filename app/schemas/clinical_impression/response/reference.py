from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class PlainClinicalImpressionReference(BaseModel):
    """Plain snake_case reference representation for ClinicalImpression references."""

    model_config = ConfigDict(extra="forbid")

    reference: str | None = Field(None, description="FHIR reference string, e.g. 'Patient/10001'.")
    type: str | None = Field(None, description="Target resource type.")
    id: int | None = Field(None, description="Resolved public sequence ID of target.")
    display: str | None = Field(None, description="Plain text narrative identifying target.")

    # 11 logical identifier fallback columns
    identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier purpose.")
    identifier_type_system: str | None = Field(None, description="Fallback identifier type system.")
    identifier_type_version: str | None = Field(None, description="Fallback identifier type version.")
    identifier_type_code: str | None = Field(None, description="Fallback identifier type code.")
    identifier_type_display: str | None = Field(None, description="Fallback identifier type display.")
    identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier user selected.")
    identifier_type_text: str | None = Field(None, description="Fallback identifier type text.")
    identifier_system: str | None = Field(None, description="Fallback identifier system.")
    identifier_value: str | None = Field(None, description="Fallback identifier value.")
    identifier_period_start: datetime | None = Field(None, description="Fallback identifier period start.")
    identifier_period_end: datetime | None = Field(None, description="Fallback identifier period end.")

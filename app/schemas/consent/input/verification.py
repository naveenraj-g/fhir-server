from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class ConsentVerificationInput(BaseModel):
    """Consent verification by patient or guardian."""

    model_config = ConfigDict(extra="forbid")

    verified: bool = Field(
        ..., description="Has been verified by patient or guardian."
    )
    verified_with: str | None = Field(
        None,
        description="Person who verified consent (Patient | RelatedPerson, e.g. 'Patient/10001').",
    )
    verified_with_display: str | None = Field(
        None, description="Plain text display for verified_with reference."
    )
    verified_with_identifier_use: IdentifierUse | None = Field(None)
    verified_with_identifier_type_system: str | None = Field(None)
    verified_with_identifier_type_version: str | None = Field(None)
    verified_with_identifier_type_code: str | None = Field(None)
    verified_with_identifier_type_display: str | None = Field(None)
    verified_with_identifier_type_text: str | None = Field(None)
    verified_with_identifier_type_user_selected: bool | None = Field(None)
    verified_with_identifier_system: str | None = Field(None)
    verified_with_identifier_value: str | None = Field(None)
    verified_with_identifier_period_start: datetime | None = Field(None)
    verified_with_identifier_period_end: datetime | None = Field(None)

    verification_date: datetime | None = Field(
        None, description="When consent verified."
    )

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRReference


class FHIRConsentVerification(BaseModel):
    """FHIR response schema for Consent.verification."""

    model_config = ConfigDict(extra="allow")

    verified: bool
    verifiedWith: FHIRReference | None = None
    verificationDate: str | None = None


class PlainConsentVerification(BaseModel):
    """Plain response schema for Consent verification."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = Field(None, description="Internal DB ID.")
    verified: bool = Field(
        ..., description="Has been verified by patient or guardian."
    )
    verified_with: str | None = Field(
        None, description="Person who verified consent."
    )
    verified_with_display: str | None = Field(
        None, description="Display name for verified_with."
    )
    verified_with_identifier_use: str | None = None
    verified_with_identifier_type_system: str | None = None
    verified_with_identifier_type_version: str | None = None
    verified_with_identifier_type_code: str | None = None
    verified_with_identifier_type_display: str | None = None
    verified_with_identifier_type_user_selected: bool | None = None
    verified_with_identifier_type_text: str | None = None
    verified_with_identifier_system: str | None = None
    verified_with_identifier_value: str | None = None
    verified_with_identifier_period_start: str | None = None
    verified_with_identifier_period_end: str | None = None

    verification_date: datetime | None = Field(
        None, description="When consent verified."
    )

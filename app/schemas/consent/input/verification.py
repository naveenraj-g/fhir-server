from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


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
    verification_date: datetime | None = Field(
        None, description="When consent verified."
    )

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.consent.response.codeable_concept import (
    PlainConsentCodeableConcept,
)


class PlainConsentIdentifier(BaseModel):
    """Plain response schema for Consent identifier."""

    model_config = ConfigDict(extra="ignore")

    id: int = Field(..., description="Internal DB ID.")
    use: str | None = Field(
        None, description="usual | official | temp | secondary | old."
    )
    type: PlainConsentCodeableConcept | None = Field(
        None, description="Identifier type."
    )
    system: str | None = Field(None, description="Namespace of identifier.")
    value: str | None = Field(None, description="Unique value.")
    period_start: datetime | None = Field(
        None, description="Validity start date."
    )
    period_end: datetime | None = Field(None, description="Validity end date.")
    assigner: str | None = Field(None, description="Organization reference.")
    assigner_display: str | None = Field(
        None, description="Plain text display for assigner."
    )

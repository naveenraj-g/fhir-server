from pydantic import BaseModel, ConfigDict, Field


class FHIRConsentPolicy(BaseModel):
    """FHIR response schema for Consent.policy."""

    model_config = ConfigDict(extra="allow")

    authority: str | None = None
    uri: str | None = None


class PlainConsentPolicy(BaseModel):
    """Plain response schema for Consent policy."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = Field(None, description="Internal DB ID.")
    authority: str | None = Field(
        None, description="Enforcement authority for policy."
    )
    uri: str | None = Field(
        None, description="Specific policy covered by this consent."
    )


class PlainConsentReference(BaseModel):
    """Plain response schema for reference items (performer, organization)."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = Field(None, description="Internal DB ID.")
    reference: str = Field(..., description="Target reference string.")
    display: str | None = Field(None, description="Display text for reference.")

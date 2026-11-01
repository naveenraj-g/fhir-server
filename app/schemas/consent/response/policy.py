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
    reference: str | None = Field(None, description="Target reference string.")
    display: str | None = Field(None, description="Display text for reference.")
    identifier_use: str | None = None
    identifier_type_system: str | None = None
    identifier_type_version: str | None = None
    identifier_type_code: str | None = None
    identifier_type_display: str | None = None
    identifier_type_user_selected: bool | None = None
    identifier_type_text: str | None = None
    identifier_system: str | None = None
    identifier_value: str | None = None
    identifier_period_start: str | None = None
    identifier_period_end: str | None = None

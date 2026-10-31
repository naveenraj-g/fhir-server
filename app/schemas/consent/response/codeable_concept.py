from pydantic import BaseModel, ConfigDict, Field


class PlainConsentCoding(BaseModel):
    """Plain response schema for Consent Coding."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = Field(None, description="Internal DB ID.")
    system: str | None = Field(None, description="Identity of terminology system.")
    version: str | None = Field(None, description="Version of the system.")
    code: str | None = Field(None, description="Symbol in syntax defined by the system.")
    display: str | None = Field(None, description="Representation defined by the system.")
    user_selected: bool | None = Field(
        None, description="If this coding was chosen directly by the user."
    )


class PlainConsentCodeableConcept(BaseModel):
    """Plain response schema for Consent CodeableConcept."""

    model_config = ConfigDict(extra="ignore")

    id: int | None = Field(None, description="Internal DB ID.")
    text: str | None = Field(None, description="Plain text representation.")
    coding: list[PlainConsentCoding] | None = Field(
        None, description="Code defined by terminology system."
    )

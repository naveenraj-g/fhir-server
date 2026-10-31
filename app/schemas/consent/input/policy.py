from pydantic import BaseModel, ConfigDict, Field


class ConsentPolicyInput(BaseModel):
    """Policies that this consent's rule conforms to."""

    model_config = ConfigDict(extra="forbid")

    authority: str | None = Field(
        None, description="Enforcement authority for policy."
    )
    uri: str | None = Field(
        None, description="Specific policy covered by this consent."
    )


class ConsentReferenceInput(BaseModel):
    """Reference input for Consent (e.g. performer, organization)."""

    model_config = ConfigDict(extra="forbid")

    reference: str = Field(
        ..., description="Literal reference (e.g. 'Organization/190001')."
    )
    display: str | None = Field(None, description="Plain text display for the reference.")

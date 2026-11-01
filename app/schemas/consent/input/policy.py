from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.repository._reference_shared import _IDENTIFIER_FALLBACK_SUFFIXES
from app.schemas.enums import IdentifierUse


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

    reference: str | None = Field(
        None, description="Literal reference (e.g. 'Organization/190001')."
    )
    display: str | None = Field(None, description="Plain text display for the reference.")
    identifier_use: IdentifierUse | None = Field(None, description="Identifier use.")
    identifier_type_system: str | None = Field(None, description="Identifier type system.")
    identifier_type_version: str | None = Field(None, description="Identifier type version.")
    identifier_type_code: str | None = Field(None, description="Identifier type code.")
    identifier_type_display: str | None = Field(None, description="Identifier type display.")
    identifier_type_user_selected: bool | None = Field(None, description="Identifier type user selected.")
    identifier_type_text: str | None = Field(None, description="Identifier type text.")
    identifier_system: str | None = Field(None, description="Identifier system.")
    identifier_value: str | None = Field(None, description="Identifier value.")
    identifier_period_start: datetime | None = Field(None, description="Identifier period start.")
    identifier_period_end: datetime | None = Field(None, description="Identifier period end.")

    @model_validator(mode="after")
    def validate_reference(self) -> "ConsentReferenceInput":
        has_ref = bool(self.reference)
        has_ident = any(
            getattr(self, suffix) is not None
            for suffix in _IDENTIFIER_FALLBACK_SUFFIXES
        )
        has_display = bool(self.display)
        if not (has_ref or has_ident or has_display):
            raise ValueError(
                "Either reference (URL), display, or at least one identifier_* field must be provided."
            )
        return self

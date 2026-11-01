from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.consent.enums import (
    ConsentDataMeaning,
    ConsentProvisionType,
)
from app.repository._reference_shared import _IDENTIFIER_FALLBACK_SUFFIXES
from app.schemas.consent.input.codeable_concept import (
    ConsentCodeableConceptInput,
    ConsentCodingInput,
)
from app.schemas.enums import IdentifierUse


class ConsentProvisionActorInput(BaseModel):
    """Who|what controlled by this rule (actor)."""

    model_config = ConfigDict(extra="forbid")

    role: ConsentCodeableConceptInput = Field(
        ..., description="How the actor is involved."
    )
    reference: str | None = Field(
        None,
        description="Resource for the actor (Device | Group | CareTeam | Organization | Patient | Practitioner | RelatedPerson | PractitionerRole, e.g. 'Practitioner/30001').",
    )
    reference_display: str | None = Field(
        None, description="Plain text display for actor reference."
    )
    reference_identifier_use: IdentifierUse | None = Field(None)
    reference_identifier_type_system: str | None = Field(None)
    reference_identifier_type_version: str | None = Field(None)
    reference_identifier_type_code: str | None = Field(None)
    reference_identifier_type_display: str | None = Field(None)
    reference_identifier_type_text: str | None = Field(None)
    reference_identifier_type_user_selected: bool | None = Field(None)
    reference_identifier_system: str | None = Field(None)
    reference_identifier_value: str | None = Field(None)
    reference_identifier_period_start: datetime | None = Field(None)
    reference_identifier_period_end: datetime | None = Field(None)

    @model_validator(mode="after")
    def validate_reference(self) -> "ConsentProvisionActorInput":
        has_ref = bool(self.reference)
        has_ident = any(
            getattr(self, f"reference_{suffix}") is not None
            for suffix in _IDENTIFIER_FALLBACK_SUFFIXES
        )
        has_display = bool(self.reference_display)
        if not (has_ref or has_ident or has_display):
            raise ValueError(
                "Either reference (URL), reference_display, or at least one reference_identifier_* field must be provided."
            )
        return self


class ConsentProvisionDataInput(BaseModel):
    """Data controlled by this rule."""

    model_config = ConfigDict(extra="forbid")

    meaning: ConsentDataMeaning = Field(
        ..., description="instance | related | dependents | authoredby."
    )
    reference: str | None = Field(
        None,
        description="The actual data reference (e.g. 'Observation/160001').",
    )
    reference_display: str | None = Field(
        None, description="Plain text display for data reference."
    )
    reference_identifier_use: IdentifierUse | None = Field(None)
    reference_identifier_type_system: str | None = Field(None)
    reference_identifier_type_version: str | None = Field(None)
    reference_identifier_type_code: str | None = Field(None)
    reference_identifier_type_display: str | None = Field(None)
    reference_identifier_type_text: str | None = Field(None)
    reference_identifier_type_user_selected: bool | None = Field(None)
    reference_identifier_system: str | None = Field(None)
    reference_identifier_value: str | None = Field(None)
    reference_identifier_period_start: datetime | None = Field(None)
    reference_identifier_period_end: datetime | None = Field(None)

    @model_validator(mode="after")
    def validate_reference(self) -> "ConsentProvisionDataInput":
        has_ref = bool(self.reference)
        has_ident = any(
            getattr(self, f"reference_{suffix}") is not None
            for suffix in _IDENTIFIER_FALLBACK_SUFFIXES
        )
        has_display = bool(self.reference_display)
        if not (has_ref or has_ident or has_display):
            raise ValueError(
                "Either reference (URL), reference_display, or at least one reference_identifier_* field must be provided."
            )
        return self


class ConsentProvisionInput(BaseModel):
    """Constraints to the base Consent.provision rule."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    type: ConsentProvisionType | None = Field(
        None, description="deny | permit."
    )
    period_start: datetime | None = Field(
        None, description="Timeframe for this rule (start)."
    )
    period_end: datetime | None = Field(
        None, description="Timeframe for this rule (end)."
    )
    actor: list[ConsentProvisionActorInput] | None = Field(
        None, description="Who|what controlled by this rule."
    )
    action: list[ConsentCodeableConceptInput] | None = Field(
        None, description="Actions controlled by this rule."
    )
    security_label: list[ConsentCodingInput] | None = Field(
        None, description="Security Labels that define affected resources."
    )
    purpose: list[ConsentCodingInput] | None = Field(
        None, description="Context of activities covered by this rule."
    )
    class_: list[ConsentCodingInput] | None = Field(
        None,
        alias="class",
        description="e.g. Resource Type, Profile, or CDA etc.",
    )
    code: list[ConsentCodeableConceptInput] | None = Field(
        None, description="e.g. If code in records, then suit this rule."
    )
    data_period_start: datetime | None = Field(
        None, description="Timeframe for data specified by this rule (start)."
    )
    data_period_end: datetime | None = Field(
        None, description="Timeframe for data specified by this rule (end)."
    )
    data: list[ConsentProvisionDataInput] | None = Field(
        None, description="Data controlled by this rule."
    )
    provision: list["ConsentProvisionInput"] | None = Field(
        None, description="Nested Exception Rules contained within this rule."
    )


ConsentProvisionInput.model_rebuild()

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class _ReferenceListInput(BaseModel):
    """Shared shape for reasonReference[] — 0..* Reference list."""

    model_config = ConfigDict(extra="forbid")

    reference: str | None = Field(None, description="FHIR reference string, e.g. 'Condition/120001'.")
    reference_display: str | None = Field(None, description="Plain text narrative identifying the target.")
    reference_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — its purpose, if known.")
    reference_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    reference_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    reference_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    reference_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    reference_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    reference_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether its type was user-selected.")
    reference_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    reference_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    reference_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    reference_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")


class ImmunizationReasonReferenceInput(_ReferenceListInput):
    """reasonReference[] — Reference(Condition|Observation|DiagnosticReport)."""


class _SingleReferenceInput(BaseModel):
    """Shared shape for patient/encounter/location/manufacturer/actor/authority/detail."""

    model_config = ConfigDict(extra="forbid")

    reference: str | None = Field(None, description="FHIR reference string, e.g. 'Patient/10001'.")
    reference_display: str | None = Field(None, description="Plain text narrative identifying the target.")
    reference_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — its purpose, if known.")
    reference_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    reference_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    reference_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    reference_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    reference_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    reference_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether its type was user-selected.")
    reference_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    reference_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    reference_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    reference_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")


class ImmunizationPatientInput(_SingleReferenceInput):
    """patient — Reference(Patient)."""


class ImmunizationEncounterInput(_SingleReferenceInput):
    """encounter — Reference(Encounter)."""


class ImmunizationLocationInput(_SingleReferenceInput):
    """location — Reference(Location)."""


class ImmunizationManufacturerInput(_SingleReferenceInput):
    """manufacturer — Reference(Organization)."""


class ImmunizationActorInput(_SingleReferenceInput):
    """performer.actor — Reference(Practitioner|PractitionerRole|Organization)."""


class ImmunizationReactionDetailInput(_SingleReferenceInput):
    """reaction.detail — Reference(Observation)."""


class ImmunizationAuthorityInput(_SingleReferenceInput):
    """protocolApplied.authority — Reference(Organization)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class _ReferenceListInput(BaseModel):
    """Shared shape for basedOn[]/partOf[]/derivedFrom[]/reasonReference[] — all 0..* Reference lists."""

    model_config = ConfigDict(extra="forbid")

    reference: str | None = Field(None, description="FHIR reference string, e.g. 'MedicationRequest/80001'.")
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


class MedicationStatementBasedOnInput(_ReferenceListInput):
    """basedOn[] — Reference(MedicationRequest|CarePlan|ServiceRequest)."""


class MedicationStatementPartOfInput(_ReferenceListInput):
    """partOf[] — Reference(MedicationAdministration|MedicationDispense|MedicationStatement|Procedure|Observation)."""


class MedicationStatementDerivedFromInput(_ReferenceListInput):
    """derivedFrom[] — Reference(Any)."""


class MedicationStatementReasonReferenceInput(_ReferenceListInput):
    """reasonReference[] — Reference(Condition|Observation|DiagnosticReport)."""


class _SingleReferenceInput(BaseModel):
    """Shared shape for subject/medication_reference/context/information_source."""

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


class MedicationStatementSubjectInput(_SingleReferenceInput):
    """subject (1..1, required at the schema layer) — Reference(Patient|Group)."""


class MedicationStatementMedicationReferenceInput(_SingleReferenceInput):
    """medication[x]'s Reference variant — Reference(Medication)."""


class MedicationStatementContextInput(_SingleReferenceInput):
    """context (0..1) — Reference(Encounter|EpisodeOfCare)."""


class MedicationStatementInformationSourceInput(_SingleReferenceInput):
    """informationSource (0..1) — Reference(Patient|Practitioner|PractitionerRole|RelatedPerson|Organization)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse

# ---------------------------------------------------------------------------
# Shared field-group shapes for every bare-Reference field on Observation —
# mirrors app.schemas.medication_request.input.reference's two base classes
# exactly.
# ---------------------------------------------------------------------------


class _ReferenceListInput(BaseModel):
    """Shared shape for basedOn[]/partOf[]/focus[]/performer[]/hasMember[]/
    derivedFrom[] — all bare 0..* Reference lists."""

    model_config = ConfigDict(extra="forbid")
    reference: str | None = Field(None, description="FHIR reference string, e.g. 'Observation/160001'.")
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


class ObservationBasedOnInput(_ReferenceListInput):
    """basedOn[] — Reference(CarePlan|DeviceRequest|ImmunizationRecommendation|MedicationRequest|NutritionOrder|ServiceRequest)."""


class ObservationPartOfInput(_ReferenceListInput):
    """partOf[] — Reference(MedicationAdministration|MedicationDispense|MedicationStatement|Procedure|Immunization|ImagingStudy)."""


class ObservationFocusInput(_ReferenceListInput):
    """focus[] — Reference(Any). Target type is never validated against an enum."""


class ObservationPerformerInput(_ReferenceListInput):
    """performer[] — Reference(Practitioner|PractitionerRole|Organization|CareTeam|Patient|RelatedPerson)."""


class ObservationHasMemberInput(_ReferenceListInput):
    """hasMember[] — Reference(Observation|QuestionnaireResponse|MolecularSequence)."""


class ObservationDerivedFromInput(_ReferenceListInput):
    """derivedFrom[] — Reference(DocumentReference|ImagingStudy|Media|QuestionnaireResponse|Observation|MolecularSequence)."""


class _SingleReferenceInput(BaseModel):
    """Shared shape for subject/encounter/specimen/device — each a bare
    0..1 Reference field."""

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


class ObservationSubjectInput(_SingleReferenceInput):
    """subject (0..1) — Reference(Patient|Group|Device|Location)."""


class ObservationEncounterInput(_SingleReferenceInput):
    """encounter (0..1) — Reference(Encounter)."""


class ObservationSpecimenInput(_SingleReferenceInput):
    """specimen (0..1) — Reference(Specimen)."""


class ObservationDeviceInput(_SingleReferenceInput):
    """device (0..1) — Reference(Device|DeviceMetric)."""

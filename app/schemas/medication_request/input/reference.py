from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse

# ---------------------------------------------------------------------------
# Shared field-group shapes for every bare-Reference field on
# MedicationRequest — mirrors app.schemas.service_request.input.reference's
# two base classes exactly.
# ---------------------------------------------------------------------------


class _ReferenceListInput(BaseModel):
    """Shared shape for basedOn[]/insurance[]/supportingInformation[]/
    reasonReference[]/detectedIssue[]/eventHistory[] — all bare 0..*
    Reference lists."""

    model_config = ConfigDict(extra="forbid")
    reference: str | None = Field(None, description="FHIR reference string, e.g. 'MedicationRequest/90001'.")
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


class MedicationRequestBasedOnInput(_ReferenceListInput):
    """basedOn[] — Reference(CarePlan|MedicationRequest|ServiceRequest|ImmunizationRecommendation)."""


class MedicationRequestReasonReferenceInput(_ReferenceListInput):
    """reasonReference[] — Reference(Condition|Observation)."""


class MedicationRequestInsuranceInput(_ReferenceListInput):
    """insurance[] — Reference(Coverage|ClaimResponse)."""


class MedicationRequestSupportingInformationInput(_ReferenceListInput):
    """supportingInformation[] — Reference(Any). Target type is never validated against an enum."""


class MedicationRequestDetectedIssueInput(_ReferenceListInput):
    """detectedIssue[] — Reference(DetectedIssue)."""


class MedicationRequestEventHistoryInput(_ReferenceListInput):
    """eventHistory[] — Reference(Provenance)."""


class _SingleReferenceInput(BaseModel):
    """Shared shape for subject/encounter/requester/performer/recorder/
    priorPrescription/dispense_request_performer — each a bare 0..1 (or
    1..1, for subject) Reference field."""

    model_config = ConfigDict(extra="forbid")
    reference: str | None = Field(None, description="FHIR reference string, e.g. 'Practitioner/30001'.")
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


class MedicationRequestSubjectInput(_SingleReferenceInput):
    """subject (1..1, required at the schema layer) — Reference(Patient|Group)."""


class MedicationRequestEncounterInput(_SingleReferenceInput):
    """encounter (0..1) — Reference(Encounter)."""


class MedicationRequestReportedReferenceInput(_SingleReferenceInput):
    """reported[x]'s Reference variant — Reference(Patient|Practitioner|PractitionerRole|RelatedPerson|Organization)."""


class MedicationRequestMedicationReferenceInput(_SingleReferenceInput):
    """medication[x]'s Reference variant — Reference(Medication)."""


class MedicationRequestRequesterInput(_SingleReferenceInput):
    """requester (0..1) — Reference(Practitioner|PractitionerRole|Organization|Patient|RelatedPerson|Device)."""


class MedicationRequestPerformerInput(_SingleReferenceInput):
    """performer (0..1) — Reference(Practitioner|PractitionerRole|Organization|Patient|Device|RelatedPerson|CareTeam)."""


class MedicationRequestRecorderInput(_SingleReferenceInput):
    """recorder (0..1) — Reference(Practitioner|PractitionerRole)."""


class MedicationRequestDispenseRequestPerformerInput(_SingleReferenceInput):
    """dispenseRequest.performer (0..1) — Reference(Organization)."""


class MedicationRequestPriorPrescriptionInput(_SingleReferenceInput):
    """priorPrescription (0..1) — Reference(MedicationRequest)."""

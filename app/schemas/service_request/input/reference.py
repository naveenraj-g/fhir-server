from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse

# ---------------------------------------------------------------------------
# Shared field-group shapes for every bare-Reference field on ServiceRequest
# — mirrors app.schemas.questionnaire_response.input.reference's two base
# classes exactly.
# ---------------------------------------------------------------------------


class _ReferenceListInput(BaseModel):
    """Shared shape for basedOn[]/replaces[]/locationReference[]/
    reasonReference[]/insurance[]/supportingInfo[]/specimen[]/
    relevantHistory[]/performer[] — all bare 0..* Reference lists."""

    model_config = ConfigDict(extra="forbid")
    reference: str | None = Field(None, description="FHIR reference string, e.g. 'ServiceRequest/80001'.")
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


class ServiceRequestBasedOnInput(_ReferenceListInput):
    """basedOn[] — Reference(CarePlan|ServiceRequest|MedicationRequest)."""


class ServiceRequestReplacesInput(_ReferenceListInput):
    """replaces[] — Reference(ServiceRequest)."""


class ServiceRequestLocationReferenceInput(_ReferenceListInput):
    """locationReference[] — Reference(Location)."""


class ServiceRequestReasonReferenceInput(_ReferenceListInput):
    """reasonReference[] — Reference(Condition|Observation|DiagnosticReport|DocumentReference)."""


class ServiceRequestInsuranceInput(_ReferenceListInput):
    """insurance[] — Reference(Coverage|ClaimResponse)."""


class ServiceRequestSupportingInfoInput(_ReferenceListInput):
    """supportingInfo[] — Reference(Any). Target type is never validated against an enum."""


class ServiceRequestSpecimenInput(_ReferenceListInput):
    """specimen[] — Reference(Specimen)."""


class ServiceRequestRelevantHistoryInput(_ReferenceListInput):
    """relevantHistory[] — Reference(Provenance)."""


class ServiceRequestPerformerInput(_ReferenceListInput):
    """performer[] — Reference(Practitioner|PractitionerRole|Organization|CareTeam|HealthcareService|Patient|Device|RelatedPerson). A plain Reference list, no wrapping BackboneElement."""


class _SingleReferenceInput(BaseModel):
    """Shared shape for subject/encounter/requester — each a bare 0..1 (or
    1..1, for subject) Reference field."""

    model_config = ConfigDict(extra="forbid")
    reference: str | None = Field(None, description="FHIR reference string, e.g. 'Location/230001'.")
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


class ServiceRequestSubjectInput(_SingleReferenceInput):
    """subject (1..1, required at the schema layer) — Reference(Patient|Group|Location|Device)."""


class ServiceRequestEncounterInput(_SingleReferenceInput):
    """encounter (0..1) — Reference(Encounter)."""


class ServiceRequestRequesterInput(_SingleReferenceInput):
    """requester (0..1) — Reference(Practitioner|PractitionerRole|Organization|Patient|RelatedPerson|Device)."""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class _SingleReferenceInput(BaseModel):
    """Shared shape for Condition reference fields."""

    model_config = ConfigDict(extra="forbid")
    reference: str | None = Field(
        None, description="FHIR reference string, e.g. 'Patient/10001'."
    )
    reference_display: str | None = Field(
        None, description="Plain text narrative identifying the target."
    )
    reference_identifier_use: IdentifierUse | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    reference_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    reference_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    reference_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )


class ConditionSubjectInput(_SingleReferenceInput):
    """Condition.subject (1..1 Reference(Patient | Group))."""


class ConditionEncounterInput(_SingleReferenceInput):
    """Condition.encounter (0..1 Reference(Encounter))."""


class ConditionRecorderInput(_SingleReferenceInput):
    """Condition.recorder (0..1 Reference(Practitioner | PractitionerRole | Patient | RelatedPerson))."""


class ConditionAsserterInput(_SingleReferenceInput):
    """Condition.asserter (0..1 Reference(Practitioner | PractitionerRole | Patient | RelatedPerson))."""


class ConditionStageAssessmentInput(_SingleReferenceInput):
    """Condition.stage.assessment (0..* Reference(ClinicalImpression | DiagnosticReport | Observation))."""


class ConditionEvidenceDetailInput(_SingleReferenceInput):
    """Condition.evidence.detail (0..* Reference(Any))."""

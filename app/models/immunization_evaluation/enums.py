from enum import Enum


class ImmunizationEvaluationStatus(str, Enum):
    """FHIR R4 ImmunizationEvaluation status.
    http://hl7.org/fhir/ValueSet/immunization-evaluation-status
    """

    completed = "completed"
    entered_in_error = "entered-in-error"


class ImmunizationEvaluationPatientReferenceType(str, Enum):
    """Allowed reference target types for ImmunizationEvaluation.patient."""

    PATIENT = "Patient"


class ImmunizationEvaluationAuthorityReferenceType(str, Enum):
    """Allowed reference target types for ImmunizationEvaluation.authority."""

    ORGANIZATION = "Organization"


class ImmunizationEvaluationImmunizationEventReferenceType(str, Enum):
    """Allowed reference target types for ImmunizationEvaluation.immunizationEvent."""

    IMMUNIZATION = "Immunization"

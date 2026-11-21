from enum import Enum


class ImmunizationEvaluationStatus(str, Enum):
    """Immunization evaluation status — stored by value, so `entered-in-error` is the
    real FHIR code."""

    completed = "completed"
    entered_in_error = "entered-in-error"

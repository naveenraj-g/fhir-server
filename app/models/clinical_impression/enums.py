from enum import Enum


class ClinicalImpressionStatus(str, Enum):
    """ClinicalImpression status (R4 clinicalimpression-status) — stored by value, so
    `in-progress` and `entered-in-error` are the real FHIR codes."""

    in_progress = "in-progress"
    completed = "completed"
    entered_in_error = "entered-in-error"

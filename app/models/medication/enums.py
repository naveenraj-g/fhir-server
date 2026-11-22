from enum import Enum


class MedicationStatus(str, Enum):
    """Medication.status (MedicationStatusCodes, required) - stored by value, so
    `entered-in-error` is the real FHIR code."""

    active = "active"
    inactive = "inactive"
    entered_in_error = "entered-in-error"

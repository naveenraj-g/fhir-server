from enum import Enum


class MedicationKnowledgeStatus(str, Enum):
    """MedicationKnowledge.status (MedicationKnowledge Status Codes, required) - stored by
    value, so `entered-in-error` is the real FHIR code.
    http://hl7.org/fhir/R4/valueset-medicationknowledge-status.html"""

    active = "active"
    inactive = "inactive"
    entered_in_error = "entered-in-error"

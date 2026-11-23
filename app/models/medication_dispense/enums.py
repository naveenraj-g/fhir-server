from enum import Enum


class MedicationDispenseStatus(str, Enum):
    """FHIR R4 MedicationDispense.status (1..1, required binding) -
    https://www.hl7.org/fhir/R4/valueset-medicationdispense-status.html

    Stored by value, so `in-progress`, `on-hold` and `entered-in-error` are the real FHIR codes."""

    preparation = "preparation"
    in_progress = "in-progress"
    cancelled = "cancelled"
    on_hold = "on-hold"
    completed = "completed"
    entered_in_error = "entered-in-error"
    stopped = "stopped"
    declined = "declined"
    unknown = "unknown"

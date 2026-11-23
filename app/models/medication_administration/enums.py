from enum import Enum


class MedicationAdministrationStatus(str, Enum):
    """FHIR R4 MedicationAdministration.status (1..1, required binding) -
    https://www.hl7.org/fhir/R4/valueset-medication-admin-status.html

    Stored by value, so `in-progress`, `not-done`, `on-hold` and `entered-in-error` are the real
    FHIR codes."""

    in_progress = "in-progress"
    not_done = "not-done"
    on_hold = "on-hold"
    completed = "completed"
    entered_in_error = "entered-in-error"
    stopped = "stopped"
    unknown = "unknown"

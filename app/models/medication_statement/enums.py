from enum import Enum


class MedicationStatementStatus(str, Enum):
    """FHIR R4 MedicationStatement.status (1..1, required binding) -
    https://www.hl7.org/fhir/R4/valueset-medication-statement-status.html

    Stored by value, so `entered-in-error`, `on-hold` and `not-taken` are the real FHIR codes."""

    active = "active"
    completed = "completed"
    entered_in_error = "entered-in-error"
    intended = "intended"
    stopped = "stopped"
    on_hold = "on-hold"
    unknown = "unknown"
    not_taken = "not-taken"

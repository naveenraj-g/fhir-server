from enum import Enum


class CommunicationStatus(str, Enum):
    """Communication.status (EventStatus, required) - stored by value, so `in-progress`, `not-done`,
    `on-hold` and `entered-in-error` are the real FHIR codes.
    https://www.hl7.org/fhir/R4/valueset-event-status.html"""

    preparation = "preparation"
    in_progress = "in-progress"
    not_done = "not-done"
    on_hold = "on-hold"
    stopped = "stopped"
    completed = "completed"
    entered_in_error = "entered-in-error"
    unknown = "unknown"

from enum import Enum


class ProcedureStatus(str, Enum):
    """Procedure event-status — stored by value, so `in-progress`, `not-done`
    and `entered-in-error` are the real FHIR codes."""

    preparation = "preparation"
    in_progress = "in-progress"
    not_done = "not-done"
    on_hold = "on-hold"
    stopped = "stopped"
    completed = "completed"
    entered_in_error = "entered-in-error"
    unknown = "unknown"

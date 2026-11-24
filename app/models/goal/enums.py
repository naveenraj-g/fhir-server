from enum import Enum


class GoalLifecycleStatus(str, Enum):
    """Goal.lifecycleStatus (GoalLifecycleStatus, required) - stored by value, so
    `on-hold` / `entered-in-error` are the real FHIR codes.
    https://www.hl7.org/fhir/R4/valueset-goal-status.html"""

    proposed = "proposed"
    planned = "planned"
    accepted = "accepted"
    active = "active"
    on_hold = "on-hold"
    completed = "completed"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"
    rejected = "rejected"

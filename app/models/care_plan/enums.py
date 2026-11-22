from enum import Enum


class CarePlanStatus(str, Enum):
    """CarePlan.status (request-status, required) - stored by value."""

    draft = "draft"
    active = "active"
    on_hold = "on-hold"
    revoked = "revoked"
    completed = "completed"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class CarePlanIntent(str, Enum):
    """CarePlan.intent (care-plan-intent, required) - stored by value."""

    proposal = "proposal"
    plan = "plan"
    order = "order"
    option = "option"

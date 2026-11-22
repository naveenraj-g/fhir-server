from enum import Enum


class MedicationRequestStatus(str, Enum):
    """MedicationRequest.status (medicationrequest-status, required) - stored by value, so
    `on-hold` and `entered-in-error` are the real FHIR codes."""

    active = "active"
    on_hold = "on-hold"
    cancelled = "cancelled"
    completed = "completed"
    entered_in_error = "entered-in-error"
    stopped = "stopped"
    draft = "draft"
    unknown = "unknown"


class MedicationRequestIntent(str, Enum):
    """MedicationRequest.intent (medicationrequest-intent, required) - stored by value, so
    `original-order`, `reflex-order`, `filler-order` and `instance-order` are the real FHIR
    codes."""

    proposal = "proposal"
    plan = "plan"
    order = "order"
    original_order = "original-order"
    reflex_order = "reflex-order"
    filler_order = "filler-order"
    instance_order = "instance-order"
    option = "option"


class MedicationRequestPriority(str, Enum):
    """MedicationRequest.priority (request-priority, required)."""

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"

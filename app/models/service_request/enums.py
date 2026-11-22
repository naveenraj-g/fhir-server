from enum import Enum


class ServiceRequestStatus(str, Enum):
    """ServiceRequest.status (RequestStatus, required) - stored by value, so
    `on-hold` and `entered-in-error` are the real FHIR codes."""

    draft = "draft"
    active = "active"
    on_hold = "on-hold"
    revoked = "revoked"
    completed = "completed"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class ServiceRequestIntent(str, Enum):
    """ServiceRequest.intent (RequestIntent, required) - stored by value, so
    `original-order`, `reflex-order`, `filler-order` and `instance-order` are the real
    FHIR codes."""

    proposal = "proposal"
    plan = "plan"
    directive = "directive"
    order = "order"
    original_order = "original-order"
    reflex_order = "reflex-order"
    filler_order = "filler-order"
    instance_order = "instance-order"
    option = "option"


class ServiceRequestPriority(str, Enum):
    """ServiceRequest.priority (RequestPriority, required)."""

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"

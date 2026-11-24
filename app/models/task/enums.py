from enum import Enum


class TaskStatus(str, Enum):
    """Task.status (TaskStatus, required) - stored by value, so `in-progress` / `on-hold` /
    `entered-in-error` are the real FHIR codes.
    https://www.hl7.org/fhir/R4/valueset-task-status.html"""

    draft = "draft"
    requested = "requested"
    received = "received"
    accepted = "accepted"
    rejected = "rejected"
    ready = "ready"
    cancelled = "cancelled"
    in_progress = "in-progress"
    on_hold = "on-hold"
    failed = "failed"
    completed = "completed"
    entered_in_error = "entered-in-error"


class TaskIntent(str, Enum):
    """Task.intent (TaskIntent, required) - stored by value.
    https://www.hl7.org/fhir/R4/valueset-task-intent.html"""

    unknown = "unknown"
    proposal = "proposal"
    plan = "plan"
    order = "order"
    original_order = "original-order"
    reflex_order = "reflex-order"
    filler_order = "filler-order"
    instance_order = "instance-order"
    option = "option"


class TaskPriority(str, Enum):
    """Task.priority (RequestPriority, required) - stored by value.
    https://www.hl7.org/fhir/R4/valueset-request-priority.html"""

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"

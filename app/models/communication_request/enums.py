from enum import Enum


class CommunicationRequestStatus(str, Enum):
    """CommunicationRequest.status (RequestStatus, required) - stored by value, so `on-hold` and
    `entered-in-error` are the real FHIR codes.
    https://www.hl7.org/fhir/R4/valueset-request-status.html"""

    draft = "draft"
    active = "active"
    on_hold = "on-hold"
    revoked = "revoked"
    completed = "completed"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class CommunicationRequestPriority(str, Enum):
    """CommunicationRequest.priority (RequestPriority, required) - stored by value.
    https://www.hl7.org/fhir/R4/valueset-request-priority.html"""

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"

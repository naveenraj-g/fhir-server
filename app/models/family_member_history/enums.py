from enum import Enum


class FamilyMemberHistoryStatus(str, Enum):
    """Family member history status — stored by value, so `entered-in-error` and
    `health-unknown` are the real FHIR codes."""

    partial = "partial"
    completed = "completed"
    entered_in_error = "entered-in-error"
    health_unknown = "health-unknown"

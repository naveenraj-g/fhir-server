from enum import Enum


class ImmunizationStatus(str, Enum):
    """Immunization event status — stored by value, so `entered-in-error` and
    `not-done` are the real FHIR codes."""

    completed = "completed"
    entered_in_error = "entered-in-error"
    not_done = "not-done"

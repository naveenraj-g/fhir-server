from enum import Enum


class SpecimenStatus(str, Enum):
    """Specimen status (R4 specimen-status) — stored by value, so `entered-in-error` is the real
    FHIR code (the old model stored `entered_in_error`)."""

    available = "available"
    unavailable = "unavailable"
    unsatisfactory = "unsatisfactory"
    entered_in_error = "entered-in-error"

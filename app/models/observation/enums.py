from enum import Enum


class ObservationStatus(str, Enum):
    """Observation status (R4 observation-status) — stored by value, so `entered-in-error` is the
    real FHIR code (the old model stored `entered_in_error`)."""

    registered = "registered"
    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    corrected = "corrected"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"
    unknown = "unknown"

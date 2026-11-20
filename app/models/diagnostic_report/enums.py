from enum import Enum


class DiagnosticReportStatus(str, Enum):
    """DiagnosticReport status — stored by value, so `entered-in-error` is the real
    FHIR code (the old model stored `entered_in_error`)."""

    registered = "registered"
    partial = "partial"
    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    corrected = "corrected"
    appended = "appended"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"
    unknown = "unknown"

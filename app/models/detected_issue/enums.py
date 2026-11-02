from enum import Enum


class DetectedIssueStatus(str, Enum):
    registered = "registered"
    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    corrected = "corrected"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class DetectedIssueSeverity(str, Enum):
    high = "high"
    moderate = "moderate"
    low = "low"


class DetectedIssuePatientReferenceType(str, Enum):
    Patient = "Patient"


class DetectedIssueAuthorReferenceType(str, Enum):
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Device = "Device"


class DetectedIssueMitigationAuthorReferenceType(str, Enum):
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"

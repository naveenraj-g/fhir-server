from enum import Enum


class RiskAssessmentStatus(str, Enum):
    """FHIR R4 RiskAssessment.status value set (required, bound to ObservationStatus):
    https://www.hl7.org/fhir/R4/valueset-observation-status.html
    """

    registered = "registered"
    preliminary = "preliminary"
    final = "final"
    amended = "amended"
    corrected = "corrected"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class RiskAssessmentConditionReferenceType(str, Enum):
    """FHIR R4 RiskAssessment.condition reference type:
    Reference(Condition).
    """

    Condition = "Condition"


class RiskAssessmentPerformerReferenceType(str, Enum):
    """FHIR R4 RiskAssessment.performer reference types:
    Reference(Practitioner | PractitionerRole | Device).
    """

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Device = "Device"


class RiskAssessmentReasonReferenceType(str, Enum):
    """FHIR R4 RiskAssessment.reasonReference reference types:
    Reference(Condition | Observation | DiagnosticReport | DocumentReference).
    """

    Condition = "Condition"
    Observation = "Observation"
    DiagnosticReport = "DiagnosticReport"
    DocumentReference = "DocumentReference"


class RiskAssessmentNoteAuthorReferenceType(str, Enum):
    """FHIR R4 RiskAssessment.note.authorReference reference types:
    Reference(Practitioner | PractitionerRole | Patient | RelatedPerson).
    """

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"

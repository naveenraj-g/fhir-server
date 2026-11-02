from enum import Enum


class ClinicalImpressionStatus(str, Enum):
    """FHIR R4 ClinicalImpression.status value set:
    https://www.hl7.org/fhir/R4/valueset-clinicalimpression-status.html
    in-progress | completed | entered-in-error
    """

    in_progress = "in-progress"
    completed = "completed"
    entered_in_error = "entered-in-error"


class ClinicalImpressionAssessorReferenceType(str, Enum):
    """FHIR R4 ClinicalImpression.assessor reference types:
    Reference(Practitioner | PractitionerRole).
    """

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"


class ClinicalImpressionPreviousReferenceType(str, Enum):
    """FHIR R4 ClinicalImpression.previous reference types:
    Reference(ClinicalImpression).
    """

    ClinicalImpression = "ClinicalImpression"


class ClinicalImpressionProblemReferenceType(str, Enum):
    """FHIR R4 ClinicalImpression.problem reference types:
    Reference(Condition | AllergyIntolerance).
    """

    Condition = "Condition"
    AllergyIntolerance = "AllergyIntolerance"


class ClinicalImpressionFindingReferenceType(str, Enum):
    """FHIR R4 ClinicalImpression.finding.itemReference reference types:
    Reference(Condition | Observation | Media).
    """

    Condition = "Condition"
    Observation = "Observation"
    Media = "Media"


class ClinicalImpressionPrognosisReferenceType(str, Enum):
    """FHIR R4 ClinicalImpression.prognosisReference reference types:
    Reference(RiskAssessment).
    """

    RiskAssessment = "RiskAssessment"


class ClinicalImpressionNoteAuthorReferenceType(str, Enum):
    """FHIR R4 ClinicalImpression.note.authorReference reference types:
    Reference(Practitioner | PractitionerRole | Patient | RelatedPerson).
    """

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"

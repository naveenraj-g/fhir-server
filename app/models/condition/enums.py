from enum import Enum


class ConditionQuantityComparator(str, Enum):
    """Bound to ConditionQuantityComparator in app.schemas.enums.
    Model-layer values are alphanumeric identifiers; schema-layer values are FHIR symbols."""

    lt = "lt"
    le = "le"
    ge = "ge"
    gt = "gt"


class ConditionRecorderReferenceType(str, Enum):
    """Condition.recorder Reference(Practitioner | PractitionerRole | Patient | RelatedPerson)."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"


class ConditionAsserterReferenceType(str, Enum):
    """Condition.asserter Reference(Practitioner | PractitionerRole | Patient | RelatedPerson)."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"


class ConditionStageAssessmentReferenceType(str, Enum):
    """Condition.stage.assessment Reference(ClinicalImpression | DiagnosticReport | Observation)."""

    ClinicalImpression = "ClinicalImpression"
    DiagnosticReport = "DiagnosticReport"
    Observation = "Observation"


class ConditionNoteAuthorReferenceType(str, Enum):
    """Condition.note.author Reference(Practitioner | PractitionerRole | Patient | RelatedPerson | Organization)."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"

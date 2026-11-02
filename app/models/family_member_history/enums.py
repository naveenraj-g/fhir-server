from enum import Enum


class FamilyMemberHistoryStatus(str, Enum):
    """FHIR R4 FamilyMemberHistory.status value set (required).

    https://www.hl7.org/fhir/R4/valueset-history-status.html
    """

    partial = "partial"
    completed = "completed"
    entered_in_error = "entered-in-error"
    health_unknown = "health-unknown"


class FamilyMemberHistoryPatientReferenceType(str, Enum):
    """FamilyMemberHistory.patient Reference(Patient)."""

    Patient = "Patient"


class FamilyMemberHistoryReasonReferenceType(str, Enum):
    """FamilyMemberHistory.reasonReference Reference(Condition | Observation | AllergyIntolerance | QuestionnaireResponse | DiagnosticReport | DocumentReference)."""

    Condition = "Condition"
    Observation = "Observation"
    AllergyIntolerance = "AllergyIntolerance"
    QuestionnaireResponse = "QuestionnaireResponse"
    DiagnosticReport = "DiagnosticReport"
    DocumentReference = "DocumentReference"


class FamilyMemberHistoryNoteAuthorReferenceType(str, Enum):
    """FamilyMemberHistory.note.author Reference(Practitioner | PractitionerRole | Patient | RelatedPerson | Organization)."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"


class FamilyMemberHistoryQuantityComparator(str, Enum):
    """Bound to FamilyMemberHistoryQuantityComparator in app.schemas.enums.
    Model-layer values are alphanumeric identifiers; schema-layer values are FHIR symbols.
    """

    lt = "lt"
    le = "le"
    ge = "ge"
    gt = "gt"

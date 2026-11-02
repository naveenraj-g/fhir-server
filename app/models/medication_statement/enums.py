from enum import Enum


class MedicationStatementStatus(str, Enum):
    """FHIR MedicationStatement.status value set (code, required) --
    https://www.hl7.org/fhir/R4/valueset-medication-statement-status.html
    """

    active = "active"
    completed = "completed"
    entered_in_error = "entered-in-error"
    intended = "intended"
    stopped = "stopped"
    on_hold = "on-hold"
    unknown = "unknown"
    not_taken = "not-taken"


class MedicationStatementSubjectReferenceType(str, Enum):
    Patient = "Patient"
    Group = "Group"


class MedicationStatementMedicationReferenceType(str, Enum):
    Medication = "Medication"


class MedicationStatementBasedOnReferenceType(str, Enum):
    MedicationRequest = "MedicationRequest"
    CarePlan = "CarePlan"
    ServiceRequest = "ServiceRequest"


class MedicationStatementPartOfReferenceType(str, Enum):
    MedicationAdministration = "MedicationAdministration"
    MedicationDispense = "MedicationDispense"
    MedicationStatement = "MedicationStatement"
    Procedure = "Procedure"
    Observation = "Observation"


class MedicationStatementContextReferenceType(str, Enum):
    Encounter = "Encounter"
    EpisodeOfCare = "EpisodeOfCare"


class MedicationStatementInformationSourceReferenceType(str, Enum):
    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"


class MedicationStatementReasonReferenceType(str, Enum):
    Condition = "Condition"
    Observation = "Observation"
    DiagnosticReport = "DiagnosticReport"


class MedicationStatementNoteAuthorReferenceType(str, Enum):
    Practitioner = "Practitioner"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"

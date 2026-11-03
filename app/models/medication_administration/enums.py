from enum import Enum


class MedicationAdministrationStatus(str, Enum):
    """FHIR MedicationAdministration.status value set (code, required) --
    https://www.hl7.org/fhir/R4/valueset-medication-admin-status.html
    """

    in_progress = "in-progress"
    not_done = "not-done"
    on_hold = "on-hold"
    completed = "completed"
    entered_in_error = "entered-in-error"
    stopped = "stopped"
    unknown = "unknown"


class MedicationAdministrationMedicationReferenceType(str, Enum):
    Medication = "Medication"


class MedicationAdministrationSubjectReferenceType(str, Enum):
    Patient = "Patient"
    Group = "Group"


class MedicationAdministrationContextReferenceType(str, Enum):
    Encounter = "Encounter"
    EpisodeOfCare = "EpisodeOfCare"


class MedicationAdministrationPartOfReferenceType(str, Enum):
    MedicationAdministration = "MedicationAdministration"
    Procedure = "Procedure"


class MedicationAdministrationPerformerActorReferenceType(str, Enum):
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Device = "Device"


class MedicationAdministrationReasonReferenceType(str, Enum):
    Condition = "Condition"
    Observation = "Observation"
    DiagnosticReport = "DiagnosticReport"


class MedicationAdministrationRequestReferenceType(str, Enum):
    MedicationRequest = "MedicationRequest"


class MedicationAdministrationDeviceReferenceType(str, Enum):
    Device = "Device"


class MedicationAdministrationNoteAuthorReferenceType(str, Enum):
    Practitioner = "Practitioner"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"


class MedicationAdministrationEventHistoryReferenceType(str, Enum):
    Provenance = "Provenance"

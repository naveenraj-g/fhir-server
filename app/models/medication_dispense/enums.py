from enum import Enum


class MedicationDispenseStatus(str, Enum):
    """FHIR MedicationDispense.status value set (code, required) --
    https://www.hl7.org/fhir/R4/valueset-medicationdispense-status.html
    """

    preparation = "preparation"
    in_progress = "in-progress"
    cancelled = "cancelled"
    on_hold = "on-hold"
    completed = "completed"
    entered_in_error = "entered-in-error"
    stopped = "stopped"
    declined = "declined"
    unknown = "unknown"


class MedicationDispensePartOfReferenceType(str, Enum):
    Procedure = "Procedure"


class MedicationDispenseStatusReasonReferenceType(str, Enum):
    DetectedIssue = "DetectedIssue"


class MedicationDispenseMedicationReferenceType(str, Enum):
    Medication = "Medication"


class MedicationDispenseSubjectReferenceType(str, Enum):
    Patient = "Patient"
    Group = "Group"


class MedicationDispenseContextReferenceType(str, Enum):
    Encounter = "Encounter"
    EpisodeOfCare = "EpisodeOfCare"


class MedicationDispensePerformerActorReferenceType(str, Enum):
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"
    Patient = "Patient"
    Device = "Device"
    RelatedPerson = "RelatedPerson"


class MedicationDispenseLocationReferenceType(str, Enum):
    Location = "Location"


class MedicationDispenseAuthorizingPrescriptionReferenceType(str, Enum):
    MedicationRequest = "MedicationRequest"


class MedicationDispenseDestinationReferenceType(str, Enum):
    Location = "Location"


class MedicationDispenseReceiverReferenceType(str, Enum):
    Patient = "Patient"
    Practitioner = "Practitioner"


class MedicationDispenseSubstitutionResponsiblePartyReferenceType(str, Enum):
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"


class MedicationDispenseDetectedIssueReferenceType(str, Enum):
    DetectedIssue = "DetectedIssue"


class MedicationDispenseEventHistoryReferenceType(str, Enum):
    Provenance = "Provenance"


class MedicationDispenseNoteAuthorReferenceType(str, Enum):
    Practitioner = "Practitioner"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"

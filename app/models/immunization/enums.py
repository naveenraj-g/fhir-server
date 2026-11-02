from enum import Enum


class ImmunizationStatus(str, Enum):
    """FHIR Immunization.status value set (code, required) --
    https://www.hl7.org/fhir/R4/valueset-immunization-status.html
    """

    completed = "completed"
    entered_in_error = "entered-in-error"
    not_done = "not-done"


class ImmunizationPatientReferenceType(str, Enum):
    Patient = "Patient"


class ImmunizationEncounterReferenceType(str, Enum):
    Encounter = "Encounter"


class ImmunizationLocationReferenceType(str, Enum):
    Location = "Location"


class ImmunizationManufacturerReferenceType(str, Enum):
    Organization = "Organization"


class ImmunizationPerformerActorReferenceType(str, Enum):
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"


class ImmunizationNoteAuthorReferenceType(str, Enum):
    Practitioner = "Practitioner"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"


class ImmunizationReasonReferenceType(str, Enum):
    Condition = "Condition"
    Observation = "Observation"
    DiagnosticReport = "DiagnosticReport"


class ImmunizationReactionDetailReferenceType(str, Enum):
    Observation = "Observation"


class ImmunizationProtocolAppliedAuthorityReferenceType(str, Enum):
    Organization = "Organization"

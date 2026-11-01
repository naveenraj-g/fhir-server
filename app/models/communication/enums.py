from enum import Enum


class CommunicationStatus(str, Enum):
    """FHIR R4 Communication.status value set (binding: event-status).
    https://www.hl7.org/fhir/R4/valueset-event-status.html
    """

    preparation = "preparation"
    in_progress = "in-progress"
    not_done = "not-done"
    on_hold = "on-hold"
    stopped = "stopped"
    completed = "completed"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class CommunicationPriority(str, Enum):
    """FHIR R4 Communication.priority value set (binding: request-priority).
    https://www.hl7.org/fhir/R4/valueset-request-priority.html
    """

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


class CommunicationSubjectReferenceType(str, Enum):
    """Allowed reference types for Communication.subject (Patient | Group)."""

    Patient = "Patient"
    Group = "Group"


class CommunicationEncounterReferenceType(str, Enum):
    """Allowed reference types for Communication.encounter (Encounter)."""

    Encounter = "Encounter"


class CommunicationSenderReferenceType(str, Enum):
    """Allowed reference types for Communication.sender (Device | Organization | Patient | Practitioner | PractitionerRole | RelatedPerson | HealthcareService)."""

    Device = "Device"
    Organization = "Organization"
    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"
    HealthcareService = "HealthcareService"


class CommunicationRecipientReferenceType(str, Enum):
    """Allowed reference types for Communication.recipient (Device | Organization | Patient | Practitioner | PractitionerRole | RelatedPerson | Group | CareTeam | HealthcareService)."""

    Device = "Device"
    Organization = "Organization"
    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"
    Group = "Group"
    CareTeam = "CareTeam"
    HealthcareService = "HealthcareService"


class CommunicationInResponseToReferenceType(str, Enum):
    """Allowed reference types for Communication.inResponseTo (Communication)."""

    Communication = "Communication"


class CommunicationReasonReferenceType(str, Enum):
    """Allowed reference types for Communication.reasonReference (Condition | Observation | DiagnosticReport | DocumentReference)."""

    Condition = "Condition"
    Observation = "Observation"
    DiagnosticReport = "DiagnosticReport"
    DocumentReference = "DocumentReference"

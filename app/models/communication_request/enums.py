from enum import Enum


class CommunicationRequestStatus(str, Enum):
    """FHIR R4 CommunicationRequest.status value set (binding: request-status).
    https://www.hl7.org/fhir/R4/valueset-request-status.html
    """

    draft = "draft"
    active = "active"
    on_hold = "on-hold"
    revoked = "revoked"
    completed = "completed"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class CommunicationRequestPriority(str, Enum):
    """FHIR R4 CommunicationRequest.priority value set (binding: request-priority).
    https://www.hl7.org/fhir/R4/valueset-request-priority.html
    """

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


class CommunicationRequestSubjectReferenceType(str, Enum):
    """Allowed reference types for CommunicationRequest.subject (Patient | Group)."""

    Patient = "Patient"
    Group = "Group"


class CommunicationRequestEncounterReferenceType(str, Enum):
    """Allowed reference types for CommunicationRequest.encounter (Encounter)."""

    Encounter = "Encounter"


class CommunicationRequestRequesterReferenceType(str, Enum):
    """Allowed reference types for CommunicationRequest.requester (Practitioner | PractitionerRole | Organization | Patient | RelatedPerson | Device)."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Device = "Device"


class CommunicationRequestRecipientReferenceType(str, Enum):
    """Allowed reference types for CommunicationRequest.recipient (Device | Organization | Patient | Practitioner | PractitionerRole | RelatedPerson | Group | CareTeam | HealthcareService)."""

    Device = "Device"
    Organization = "Organization"
    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"
    Group = "Group"
    CareTeam = "CareTeam"
    HealthcareService = "HealthcareService"


class CommunicationRequestSenderReferenceType(str, Enum):
    """Allowed reference types for CommunicationRequest.sender (Device | Organization | Patient | Practitioner | PractitionerRole | RelatedPerson | HealthcareService)."""

    Device = "Device"
    Organization = "Organization"
    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"
    HealthcareService = "HealthcareService"


class CommunicationRequestReasonReferenceType(str, Enum):
    """Allowed reference types for CommunicationRequest.reasonReference (Condition | Observation | DiagnosticReport | DocumentReference)."""

    Condition = "Condition"
    Observation = "Observation"
    DiagnosticReport = "DiagnosticReport"
    DocumentReference = "DocumentReference"

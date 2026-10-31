from enum import Enum


class TaskStatus(str, Enum):
    """FHIR R4 TaskStatus value set (required binding).
    https://www.hl7.org/fhir/R4/valueset-task-status.html
    """

    draft = "draft"
    requested = "requested"
    received = "received"
    accepted = "accepted"
    rejected = "rejected"
    ready = "ready"
    cancelled = "cancelled"
    in_progress = "in-progress"
    on_hold = "on-hold"
    failed = "failed"
    completed = "completed"
    entered_in_error = "entered-in-error"


class TaskIntent(str, Enum):
    """FHIR R4 TaskIntent value set (required binding).
    https://www.hl7.org/fhir/R4/valueset-task-intent.html
    """

    unknown = "unknown"
    proposal = "proposal"
    plan = "plan"
    order = "order"
    original_order = "original-order"
    reflex_order = "reflex-order"
    filler_order = "filler-order"
    instance_order = "instance-order"
    option = "option"


class TaskPriority(str, Enum):
    """FHIR R4 RequestPriority value set (required binding).
    https://www.hl7.org/fhir/R4/valueset-request-priority.html
    """

    routine = "routine"
    urgent = "urgent"
    asap = "asap"
    stat = "stat"


class TaskRequesterReferenceType(str, Enum):
    """Allowed reference types for Task.requester (Device|Organization|Patient|Practitioner|PractitionerRole|RelatedPerson)."""

    Device = "Device"
    Organization = "Organization"
    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"


class TaskOwnerReferenceType(str, Enum):
    """Allowed reference types for Task.owner (Practitioner|PractitionerRole|Organization|CareTeam|HealthcareService|Patient|Device|RelatedPerson)."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"
    CareTeam = "CareTeam"
    HealthcareService = "HealthcareService"
    Patient = "Patient"
    Device = "Device"
    RelatedPerson = "RelatedPerson"


class TaskLocationReferenceType(str, Enum):
    """Allowed reference types for Task.location (Location)."""

    Location = "Location"


class TaskEncounterReferenceType(str, Enum):
    """Allowed reference types for Task.encounter (Encounter)."""

    Encounter = "Encounter"


class TaskRestrictionRecipientReferenceType(str, Enum):
    """Allowed reference types for Task.restriction.recipient (Patient|Practitioner|PractitionerRole|RelatedPerson|Group|Organization)."""

    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"
    Group = "Group"
    Organization = "Organization"


class TaskInsuranceReferenceType(str, Enum):
    """Allowed reference types for Task.insurance (Coverage|ClaimResponse)."""

    Coverage = "Coverage"
    ClaimResponse = "ClaimResponse"


class TaskRelevantHistoryReferenceType(str, Enum):
    """Allowed reference types for Task.relevantHistory (Provenance)."""

    Provenance = "Provenance"


class TaskPartOfReferenceType(str, Enum):
    """Allowed reference types for Task.partOf (Task)."""

    Task = "Task"

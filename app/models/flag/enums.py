from enum import Enum


class FlagStatus(str, Enum):
    """Allowed values for Flag.status (1..1 code, binding: flag-status)."""

    active = "active"
    inactive = "inactive"
    entered_in_error = "entered-in-error"


class FlagSubjectReferenceType(str, Enum):
    """Allowed reference types for Flag.subject (1..1 Reference(Patient|Location|Group|Organization|Practitioner|PlanDefinition|Medication|Procedure))."""

    Patient = "Patient"
    Location = "Location"
    Group = "Group"
    Organization = "Organization"
    Practitioner = "Practitioner"
    PlanDefinition = "PlanDefinition"
    Medication = "Medication"
    Procedure = "Procedure"


class FlagAuthorReferenceType(str, Enum):
    """Allowed reference types for Flag.author (0..1 Reference(Device|Organization|Patient|Practitioner|PractitionerRole))."""

    Device = "Device"
    Organization = "Organization"
    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"


class FlagEncounterReferenceType(str, Enum):
    """Allowed reference types for Flag.encounter (0..1 Reference(Encounter))."""

    Encounter = "Encounter"

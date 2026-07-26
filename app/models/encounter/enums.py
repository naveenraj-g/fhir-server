from enum import Enum


class EncounterStatus(str, Enum):
    """FHIR R4 Encounter status value set (required binding)."""

    planned = "planned"
    arrived = "arrived"
    triaged = "triaged"
    in_progress = "in-progress"
    onleave = "onleave"
    finished = "finished"
    cancelled = "cancelled"
    entered_in_error = "entered-in-error"
    unknown = "unknown"


class EncounterLocationStatus(str, Enum):
    """FHIR Encounter location status value set."""

    planned = "planned"
    active = "active"
    reserved = "reserved"
    completed = "completed"


class EncounterParticipantReferenceType(str, Enum):
    """FHIR R4 reference types for Encounter.participant.individual."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"


class EncounterBasedOnReferenceType(str, Enum):
    """FHIR R4 reference types for Encounter.basedOn."""

    ServiceRequest = "ServiceRequest"


class EncounterDiagnosisConditionType(str, Enum):
    """FHIR R4 reference types for Encounter.diagnosis.condition."""

    Condition = "Condition"
    Procedure = "Procedure"


class EncounterReasonReferenceType(str, Enum):
    """FHIR R4 reference types for Encounter.reasonReference."""

    Condition = "Condition"
    Procedure = "Procedure"
    Observation = "Observation"
    ImmunizationRecommendation = "ImmunizationRecommendation"


class EncounterEpisodeOfCareReferenceType(str, Enum):
    """Allowed reference types for Encounter.episodeOfCare[]."""

    EpisodeOfCare = "EpisodeOfCare"


class EncounterAppointmentReferenceType(str, Enum):
    """Allowed reference types for Encounter.appointment[]."""

    Appointment = "Appointment"


class EncounterAccountReferenceType(str, Enum):
    """Allowed reference types for Encounter.account[]."""

    Account = "Account"


class EncounterLocationReferenceType(str, Enum):
    """Allowed reference types for Encounter.location[].location."""

    Location = "Location"

from enum import Enum


class CareTeamStatus(str, Enum):
    """FHIR CareTeam.status value set (code, required) —
    http://hl7.org/fhir/care-team-status
    """

    proposed = "proposed"
    active = "active"
    suspended = "suspended"
    inactive = "inactive"
    entered_in_error = "entered-in-error"


class CareTeamSubjectReferenceType(str, Enum):
    """CareTeam.subject Reference(Patient | Group)."""

    Patient = "Patient"
    Group = "Group"


class CareTeamEncounterReferenceType(str, Enum):
    """CareTeam.encounter Reference(Encounter)."""

    Encounter = "Encounter"


class CareTeamParticipantMemberReferenceType(str, Enum):
    """CareTeam.participant.member Reference(Practitioner | PractitionerRole | RelatedPerson | Patient | Organization | CareTeam)."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    RelatedPerson = "RelatedPerson"
    Patient = "Patient"
    Organization = "Organization"
    CareTeam = "CareTeam"


class CareTeamParticipantOnBehalfOfReferenceType(str, Enum):
    """CareTeam.participant.onBehalfOf Reference(Organization)."""

    Organization = "Organization"


class CareTeamReasonReferenceType(str, Enum):
    """CareTeam.reasonReference Reference(Condition)."""

    Condition = "Condition"


class CareTeamManagingOrganizationReferenceType(str, Enum):
    """CareTeam.managingOrganization Reference(Organization)."""

    Organization = "Organization"


class CareTeamAssignerReferenceType(str, Enum):
    """CareTeam.identifier.assigner Reference(Organization)."""

    Organization = "Organization"


class CareTeamNoteAuthorReferenceType(str, Enum):
    """CareTeam.note.author Reference(Practitioner | Patient | RelatedPerson | Organization)."""

    Practitioner = "Practitioner"
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"
    Organization = "Organization"

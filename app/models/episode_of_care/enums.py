from enum import Enum

from app.schemas.enums import EpisodeOfCareStatus


class EpisodeOfCarePatientReferenceType(str, Enum):
    """EpisodeOfCare.patient Reference(Patient)."""

    Patient = "Patient"


class EpisodeOfCareManagingOrganizationReferenceType(str, Enum):
    """EpisodeOfCare.managingOrganization Reference(Organization)."""

    Organization = "Organization"


class EpisodeOfCareCareManagerReferenceType(str, Enum):
    """EpisodeOfCare.careManager Reference(Practitioner | PractitionerRole)."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"


class EpisodeOfCareReferralRequestReferenceType(str, Enum):
    """EpisodeOfCare.referralRequest Reference(ServiceRequest)."""

    ServiceRequest = "ServiceRequest"


class EpisodeOfCareTeamReferenceType(str, Enum):
    """EpisodeOfCare.team Reference(CareTeam)."""

    CareTeam = "CareTeam"


class EpisodeOfCareAccountReferenceType(str, Enum):
    """EpisodeOfCare.account Reference(Account)."""

    Account = "Account"


class EpisodeOfCareDiagnosisConditionReferenceType(str, Enum):
    """EpisodeOfCare.diagnosis.condition Reference(Condition)."""

    Condition = "Condition"


class EpisodeOfCareAssignerReferenceType(str, Enum):
    """EpisodeOfCare.identifier.assigner Reference(Organization)."""

    Organization = "Organization"

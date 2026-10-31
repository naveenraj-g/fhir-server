from enum import Enum


class ConsentStatus(str, Enum):
    draft = "draft"
    proposed = "proposed"
    active = "active"
    rejected = "rejected"
    inactive = "inactive"
    entered_in_error = "entered-in-error"


class ConsentPatientReferenceType(str, Enum):
    Patient = "Patient"


class ConsentPerformerReferenceType(str, Enum):
    Organization = "Organization"
    Patient = "Patient"
    Practitioner = "Practitioner"
    RelatedPerson = "RelatedPerson"
    PractitionerRole = "PractitionerRole"


class ConsentSourceReferenceType(str, Enum):
    Consent = "Consent"
    DocumentReference = "DocumentReference"
    Contract = "Contract"
    QuestionnaireResponse = "QuestionnaireResponse"


class ConsentVerifiedWithReferenceType(str, Enum):
    Patient = "Patient"
    RelatedPerson = "RelatedPerson"


class ConsentProvisionType(str, Enum):
    deny = "deny"
    permit = "permit"


class ConsentProvisionActorReferenceType(str, Enum):
    Device = "Device"
    Group = "Group"
    CareTeam = "CareTeam"
    Organization = "Organization"
    Patient = "Patient"
    Practitioner = "Practitioner"
    RelatedPerson = "RelatedPerson"
    PractitionerRole = "PractitionerRole"


class ConsentDataMeaning(str, Enum):
    instance = "instance"
    related = "related"
    dependents = "dependents"
    authoredby = "authoredby"

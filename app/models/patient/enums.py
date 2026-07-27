from enum import Enum


class AddressUse(str, Enum):
    """FHIR AddressUse value set — the purpose of this address."""

    home = "home"
    work = "work"
    temp = "temp"
    old = "old"
    billing = "billing"


class AddressType(str, Enum):
    """FHIR AddressType value set — the type of address."""

    postal = "postal"
    physical = "physical"
    both = "both"


class ContactPointSystem(str, Enum):
    """FHIR ContactPointSystem value set — telecommunications form for contact point."""

    phone = "phone"
    fax = "fax"
    email = "email"
    pager = "pager"
    url = "url"
    sms = "sms"
    other = "other"


class ContactPointUse(str, Enum):
    """FHIR ContactPointUse value set — purpose of the contact point."""

    home = "home"
    work = "work"
    temp = "temp"
    old = "old"
    mobile = "mobile"


class HumanNameUse(str, Enum):
    """FHIR HumanNameUse value set — indicates the purpose of this name."""

    usual = "usual"
    official = "official"
    temp = "temp"
    nickname = "nickname"
    anonymous = "anonymous"
    old = "old"
    maiden = "maiden"


class PatientGender(str, Enum):
    """FHIR R4 administrative gender (used by Patient.gender and Patient.contact.gender)."""

    male = "male"
    female = "female"
    other = "other"
    unknown = "unknown"


class PatientLinkType(str, Enum):
    """FHIR R4 link type codes for Patient.link.type."""

    replaced_by = "replaced-by"
    replaces = "replaces"
    refer = "refer"
    seealso = "seealso"


class PatientGeneralPractitionerType(str, Enum):
    """Allowed reference types for Patient.generalPractitioner."""

    Organization = "Organization"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"


class PatientLinkOtherType(str, Enum):
    """Allowed reference types for Patient.link.other."""

    Patient = "Patient"
    RelatedPerson = "RelatedPerson"

from enum import Enum

# datatype enums


class AddressUse(str, Enum):
    """
    FHIR AddressUse value set.

    The purpose of this address.
    """

    home = "home"
    work = "work"
    temp = "temp"
    old = "old"
    billing = "billing"


class AddressType(str, Enum):
    """
    FHIR AddressType value set.

    The type of address.
    """

    postal = "postal"
    physical = "physical"
    both = "both"


class AdministrativeGender(str, Enum):
    """
    FHIR AdministrativeGender value set.

    The gender of a person for administrative purposes.
    """

    male = "male"
    female = "female"
    other = "other"
    unknown = "unknown"


class ContactPointSystem(str, Enum):
    """
    FHIR ContactPointSystem value set.

    Telecommunications form for contact point.
    """

    phone = "phone"
    fax = "fax"
    email = "email"
    pager = "pager"
    url = "url"
    sms = "sms"
    other = "other"


class ContactPointUse(str, Enum):
    """
    FHIR ContactPointUse value set.

    Purpose of the contact point.
    """

    home = "home"
    work = "work"
    temp = "temp"
    old = "old"
    mobile = "mobile"


class HumanNameUse(str, Enum):
    """
    FHIR HumanNameUse value set.

    Indicates the purpose of this name.
    """

    usual = "usual"  # The name normally used
    official = "official"  # Official/legal name
    temp = "temp"  # Temporary name
    nickname = "nickname"  # Nickname
    anonymous = "anonymous"  # Anonymous/pseudonym
    old = "old"  # Old/previous name
    maiden = "maiden"  # Maiden name


class IdentifierUse(str, Enum):
    """
    FHIR IdentifierUse value set.

    Indicates the purpose of the identifier.
    """

    usual = "usual"  # The identifier the resource owner normally uses
    official = (
        "official"  # The identifier considered official for legal/administrative use
    )
    temp = "temp"  # Temporary identifier
    secondary = "secondary"  # Additional identifier
    old = "old"  # No longer valid identifier


"""
------------------------------------------------------------------------------
------------------------------------------------------------------------------
"""
# backbone enums


class PatientLinkType(str, Enum):
    """
    FHIR Patient.link.type value set.
    """

    replaced_by = "replaced-by"
    replaces = "replaces"
    refer = "refer"
    seealso = "seealso"


class HealthcareServiceDayOfWeek(str, Enum):
    """
    FHIR DaysOfWeek value set — used by HealthcareService.availableTime.daysOfWeek.
    """

    mon = "mon"
    tue = "tue"
    wed = "wed"
    thu = "thu"
    fri = "fri"
    sat = "sat"
    sun = "sun"


class PractitionerRoleDayOfWeek(str, Enum):
    """
    FHIR DaysOfWeek value set — used by PractitionerRole.availableTime.daysOfWeek.
    """

    mon = "mon"
    tue = "tue"
    wed = "wed"
    thu = "thu"
    fri = "fri"
    sat = "sat"
    sun = "sun"


class SlotStatus(str, Enum):
    """
    FHIR Slot.status value set — https://www.hl7.org/fhir/R4/valueset-slotstatus.html

    Member name uses underscores (valid Python identifiers can't contain
    hyphens); the stored `.value` is the true hyphenated FHIR wire code —
    same key!=value shape as PatientLinkType above. The model-layer
    app.models.slot.enums.SlotStatus is a *different* enum with matching
    member NAMES but underscore-only values (see that class's docstring
    for why) — convert between them by member name, e.g.
    `ModelSlotStatus[payload.status.name]`, never by value.
    """

    busy = "busy"
    free = "free"
    busy_unavailable = "busy-unavailable"
    busy_tentative = "busy-tentative"
    entered_in_error = "entered-in-error"

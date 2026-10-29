from enum import Enum


class HealthcareServiceLocationReferenceType(str, Enum):
    """Allowed reference type for HealthcareService.location[] (0..*) — a
    HealthcareService is only ever delivered at a Location."""

    Location = "Location"


class HealthcareServiceCoverageAreaReferenceType(str, Enum):
    """Allowed reference type for HealthcareService.coverageArea[] (0..*)."""

    Location = "Location"


class HealthcareServiceEndpointReferenceType(str, Enum):
    """Allowed reference type for HealthcareService.endpoint[] (0..*).

    Endpoint is not a modeled resource in this system, so in practice rows
    carry the reference_identifier_* logical-reference columns rather than a
    resolved reference_id. The enum still exists so the allowed target type is
    self-documenting and the reference pattern stays uniform — same reasoning
    as OrganizationEndpointReferenceType / LocationEndpointReferenceType.
    """

    Endpoint = "Endpoint"


class HealthcareServiceDayOfWeek(str, Enum):
    """FHIR R4 HealthcareService.availableTime.daysOfWeek (0..*, required
    binding).

    A `required` binding is a closed code list — HL7 defines the entire
    allowed value set, with no room for a deployment or profile to extend
    it — so this is bound to a real Postgres `ARRAY(Enum)` column
    (`healthcare_service_day_of_week` type, see
    `HealthcareServiceAvailableTime`), the same way every *single*-value
    code column in this codebase already is. See `LocationDayOfWeek`'s
    docstring (`app/models/location/enums.py`) for the full reasoning this
    mirrors.
    https://www.hl7.org/fhir/R4/valueset-days-of-week.html
    """

    mon = "mon"
    tue = "tue"
    wed = "wed"
    thu = "thu"
    fri = "fri"
    sat = "sat"
    sun = "sun"

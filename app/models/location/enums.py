from enum import Enum


class LocationStatus(str, Enum):
    """FHIR R4 Location.status (0..1, required binding) — general availability
    of the location.
    https://www.hl7.org/fhir/R4/valueset-location-status.html
    """

    active = "active"
    suspended = "suspended"
    inactive = "inactive"


class LocationMode(str, Enum):
    """FHIR R4 Location.mode (0..1, required binding) — whether the row
    describes one specific place ("instance") or a class of places ("kind",
    e.g. "a general ward bed").
    https://www.hl7.org/fhir/R4/valueset-location-mode.html
    """

    instance = "instance"
    kind = "kind"


class LocationPartOfReferenceType(str, Enum):
    """Allowed reference type for Location.partOf (0..1) — a Location is only
    ever physically contained by another Location."""

    Location = "Location"


class LocationEndpointReferenceType(str, Enum):
    """Allowed reference type for Location.endpoint[] (0..*).

    Endpoint is not a modeled resource in this system, so in practice rows
    carry the reference_identifier_* logical-reference columns rather than a
    resolved reference_id. The enum still exists so the allowed target type is
    self-documenting and the reference pattern stays uniform — same reasoning
    as OrganizationEndpointReferenceType.
    """

    Endpoint = "Endpoint"


class LocationDayOfWeek(str, Enum):
    """FHIR R4 Location.hoursOfOperation.daysOfWeek (0..*, required binding).

    Stored comma-separated in a single Text column per the `daysOfWeek[]`
    exception in /fhir-db-model, so this enum is not bound to a PostgreSQL
    type — it exists for schema-layer validation and mapper round-tripping.
    https://www.hl7.org/fhir/R4/valueset-days-of-week.html
    """

    mon = "mon"
    tue = "tue"
    wed = "wed"
    thu = "thu"
    fri = "fri"
    sat = "sat"
    sun = "sun"

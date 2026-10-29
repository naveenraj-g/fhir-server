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

    A `required` binding is a closed code list — HL7 defines the entire
    allowed value set, with no room for a deployment or profile to extend
    it — so unlike every other `ARRAY(String)` scalar list in this project
    (`Address.line`, `HumanName.given`/`prefix`/`suffix`, none of which carry
    any binding at all), this one is bound to a real Postgres `ARRAY(Enum)`
    column (`location_day_of_week` type, see `LocationHoursOfOperation`), the
    same way every *single*-value code column in this codebase already is
    (`LocationModel.status`/`.mode`, etc.) — enforcing a spec-defined closed
    enumeration at the DB layer isn't "inventing a rule beyond spec," it's
    mirroring the required binding verbatim. This enum is still what the
    Pydantic schema layer validates against and the mapper round-trips
    through; it's just no longer schema-layer-only.
    https://www.hl7.org/fhir/R4/valueset-days-of-week.html
    """

    mon = "mon"
    tue = "tue"
    wed = "wed"
    thu = "thu"
    fri = "fri"
    sat = "sat"
    sun = "sun"

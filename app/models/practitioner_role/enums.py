from enum import Enum


class PractitionerRoleLocationReferenceType(str, Enum):
    """Allowed reference type for PractitionerRole.location[] (0..*) — a
    PractitionerRole is only ever delivered at a Location."""

    Location = "Location"


class PractitionerRoleHealthcareServiceReferenceType(str, Enum):
    """Allowed reference type for PractitionerRole.healthcareService[] (0..*)."""

    HealthcareService = "HealthcareService"


class PractitionerRoleEndpointReferenceType(str, Enum):
    """Allowed reference type for PractitionerRole.endpoint[] (0..*).

    Endpoint is not a modeled resource in this system, so in practice rows
    carry the reference_identifier_* logical-reference columns rather than a
    resolved reference_id — same reasoning as
    HealthcareServiceEndpointReferenceType.
    """

    Endpoint = "Endpoint"


class PractitionerRoleDayOfWeek(str, Enum):
    """FHIR R4 PractitionerRole.availableTime.daysOfWeek (0..*, required
    binding).

    A `required` binding is a closed code list — HL7 defines the entire
    allowed value set, with no room for a deployment or profile to extend
    it — so this is bound to a real Postgres `ARRAY(Enum)` column
    (`practitioner_role_day_of_week` type, see
    `PractitionerRoleAvailableTime`), the same way every *single*-value
    code column in this codebase already is. See `LocationDayOfWeek`'s
    docstring (`app/models/location/enums.py`) for the full reasoning this
    mirrors. A separate, independent copy of this enum also lives at
    `app.schemas.enums.PractitionerRoleDayOfWeek` (the Pydantic schema
    layer's own source of truth, same two-copies-per-layer situation as
    `IdentifierUse` — not a pattern to merge away, see CLAUDE.md).
    https://www.hl7.org/fhir/R4/valueset-days-of-week.html
    """

    mon = "mon"
    tue = "tue"
    wed = "wed"
    thu = "thu"
    fri = "fri"
    sat = "sat"
    sun = "sun"

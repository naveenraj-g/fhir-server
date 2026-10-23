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

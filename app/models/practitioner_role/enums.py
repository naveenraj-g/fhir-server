from enum import Enum


class PractitionerRoleLocationReferenceType(str, Enum):
    """Allowed reference type for PractitionerRole.location[] (0..*) — used to
    parse and existence-check a relative `Location/<id>`."""

    Location = "Location"


class PractitionerRoleHealthcareServiceReferenceType(str, Enum):
    """Allowed reference type for PractitionerRole.healthcareService[] (0..*)."""

    HealthcareService = "HealthcareService"


class PractitionerRoleEndpointReferenceType(str, Enum):
    """Allowed reference type for PractitionerRole.endpoint[] (0..*).

    Endpoint is a resource on this server, so a relative `Endpoint/<id>` is
    resolved (and existence-checked on write); an endpoint given only by
    identifier, or by an absolute URL, carries no resolved reference_id.
    """

    Endpoint = "Endpoint"

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

    Endpoint is a resource on this server, so a relative `Endpoint/<id>` is
    resolved (and existence-checked on write); an endpoint given only by
    identifier, or by an absolute URL, carries no resolved reference_id. The
    enum keeps the allowed target type self-documenting and the reference
    pattern uniform.
    """

    Endpoint = "Endpoint"

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

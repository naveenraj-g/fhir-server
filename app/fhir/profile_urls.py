"""Canonical URL construction for this project's own country/organization
profile layers — shared by app.fhir.validation.dispatch (the fallback URL
used when resolving which profile to validate a resource against) and
app.services.fhir_profile.core (auto-deriving a new or edited
organization-scope profile's own canonical url, server-side, never trusted
from the request). Kept in one place so FhirValidationConfig's
canonical_base_url only has to be read in one spot — change that one
setting and both country-layer and organization-layer URLs repoint
together.

Base R4's own canonical URL (http://hl7.org/fhir/StructureDefinition/{type})
is NOT here — that's HL7's real, external namespace, never derived from
this project's own canonical_base_url setting. See
app.fhir.validation.dispatch's _BASE_PROFILE_URL.
"""

from app.core.config import settings


def country_profile_url(country: str, resource_type: str) -> str:
    return (
        f"{settings.fhir_validation.canonical_base_url}/fhir/StructureDefinition/"
        f"{country.lower()}-{resource_type.lower()}"
    )


def organization_profile_url(org_id: str, resource_type: str) -> str:
    return (
        f"{settings.fhir_validation.canonical_base_url}/fhir/StructureDefinition/"
        f"org-{org_id}-{resource_type.lower()}"
    )

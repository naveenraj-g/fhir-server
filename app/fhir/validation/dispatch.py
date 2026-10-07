"""Single entrypoint callers should use instead of reaching for
base_r4.validate_base_r4() or java_validator.validate_via_java() directly —
picks the backend AND, when applicable, the country-layer profile, so a
resource service never needs to know or care which one is active. See
docs/structure-definitions/12-three-layer-validation-architecture.md.

Country selection is a single, global, deploy-time setting
(settings.fhir_validation.country) — not resolved per-request from the
payload or from a per-tenant lookup. This is a deliberate choice: a value
inside the payload being validated (e.g. Organization.address.country)
can't be trusted to pick which rules validate that same payload, and this
project is deployed single-tenant-per-instance (one hospital, or one
country rollout, per deployment) rather than multi-tenant-per-country — so
"which country" is exactly as static as "which routes are enabled"
(app/core/config.py's RoutesConfig), not something to resolve dynamically.
Swapping which country a deployment serves is one config edit, same as
flipping `backend`.
"""

from app.core.config import settings
from app.core.logging import get_logger
from app.fhir.validation.base_r4 import validate_base_r4
from app.fhir.validation.java_validator import profile_exists, validate_via_java

logger = get_logger(__name__)

# Base R4's own canonical URL is fixed per resource type and never varies by
# tenant/country — this is the one HL7 publishes and the sidecar already has
# preloaded (confirmed via its own GET /profiles).
_BASE_PROFILE_URL = "http://hl7.org/fhir/StructureDefinition/{resource_type}"

# Country-layer profiles are this project's own, not HL7-published — see
# app/fhir/profiling/README.md. URL and on-disk layer name both derive from
# (country, resource_type) by this one convention; nothing reads a file just
# to discover its own URL.
_COUNTRY_PROFILE_URL = "https://fhir-server.dev/fhir/StructureDefinition/{country}-{resource_type}"


def _country_layer(country: str) -> str:
    return f"country_{country.lower()}"


async def validate_resource(resource_type: str, fhir_resource: dict) -> list[dict]:
    """Validates `fhir_resource` (true FHIR JSON) against `resource_type`'s
    most specific applicable profile, using whichever backend
    settings.fhir_validation.backend selects. Returns a list of
    {"field", "message"} dicts, empty when valid — identical shape
    regardless of backend or which layer actually fired.

    Resolution order for "java_validator", per resource_type:
      1. If settings.fhir_validation.country is set AND a
         country_<code>.json exists for this resource_type, validate against
         that profile's URL. The sidecar walks baseDefinition itself (already
         confirmed), so base R4's own invariants (org-1/org-2/org-3 for
         Organization) still apply underneath — naming the country profile is
         enough, the base layer is never named directly here.
      2. Otherwise (no country configured, or this resource_type has no
         country-layer file yet), fall back to the plain base R4 profile —
         same behavior as before country profiles existed at all.

    "native" never considers country at all — it has no concept of profiles,
    by design (see base_r4.py's module docstring)."""
    if settings.fhir_validation.backend == "java_validator":
        country = settings.fhir_validation.country
        if country and profile_exists(resource_type, _country_layer(country)):
            profile_url = _COUNTRY_PROFILE_URL.format(
                country=country.lower(), resource_type=resource_type.lower()
            )
            layer = _country_layer(country)
        else:
            if country:
                logger.info(
                    "No country-layer profile for this resource type — falling back to base R4",
                    extra={
                        "event": "fhir_validation.country_profile_missing",
                        "resource_type": resource_type,
                        "country": country,
                    },
                )
            profile_url = _BASE_PROFILE_URL.format(resource_type=resource_type)
            layer = None
        return await validate_via_java(
            resource_type, fhir_resource, profile_url=profile_url, layer=layer
        )
    return validate_base_r4(resource_type, fhir_resource)

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

The country-layer StructureDefinition itself comes from the fhir_profile DB
table, through FhirProfileService's cache-aside read (base: never
invalidated; country: invalidated on write once an admin edit path exists —
see that service's own docstring) — not from the file-based
scripts/data/profiling/ convention that stood in for it before that table
existed. This module is the only caller that resolves it, so
java_validator.py's registration path stays a plain "register this dict"
step with no DB/cache concerns of its own.
"""

from fastapi.encoders import jsonable_encoder

from app.core.config import settings
from app.core.logging import get_logger
from app.fhir.profile_urls import country_profile_url, organization_profile_url
from app.fhir.validation.base_r4 import validate_base_r4
from app.fhir.validation.java_validator import (
    ensure_profile_registered,
    validate_via_java,
)
from app.models.fhir_profile.enums import FhirProfileScopeLevel, FhirProfileStatus

logger = get_logger(__name__)

# Base R4's own canonical URL is fixed per resource type and never varies by
# tenant/country — this is the one HL7 publishes and the sidecar already has
# preloaded (confirmed via its own GET /profiles).
_BASE_PROFILE_URL = "http://hl7.org/fhir/StructureDefinition/{resource_type}"

# Country/organization-layer profile URLs are this project's own, not
# HL7-published — see scripts/data/profiling/README.md and
# app.fhir.profile_urls (shared with app.services.fhir_profile.core, which
# auto-derives the same organization-layer URL at profile-creation/edit
# time). Nothing fetches a profile just to discover its own URL — though
# the row's own "url" field (from FhirProfileService) is used verbatim when
# present, since it's the authoritative value; these functions are just
# the fallback/check below.


def _country_layer(country: str) -> str:
    return f"country_{country.lower()}"


def _organization_layer(org_id: str) -> str:
    return f"organization_{org_id}"


async def _country_structure_definition(
    resource_type: str, country: str
) -> dict | None:
    # Deferred import: app.di.container imports, transitively (through
    # app.di.modules -> every resource's service, including this
    # validation path itself), this exact module — a genuine cycle at
    # module-load time. By the time this function actually runs (a real
    # request, always after the whole app has finished importing), the
    # container module is fully initialized, so the import is safe here.
    from app.di.container import container

    service = container.fhir_profile.fhir_profile_service()
    return await service.get_country_profile(resource_type, country)


async def _organization_structure_definition(
    resource_type: str, org_id: str
) -> dict | None:
    # Same deferred-import reason as _country_structure_definition() above.
    from app.di.container import container

    service = container.fhir_profile.fhir_profile_service()
    return await service.get_organization_profile(resource_type, org_id)


async def register_configured_country_profiles() -> None:
    """Called once from app/main.py's lifespan() at application startup —
    NOT from validate_resource() or anywhere per-request.

    Eagerly warms FhirProfileService's cache-aside layer AND proactively
    registers with the Java validator sidecar every resource_type's
    active country profile for this deployment's single configured
    country (settings.fhir_validation.country). This closes a real
    cold-start race: without it, whichever resource_type happens to get
    validated first after a fresh boot decides what gets registered with
    the sidecar — and an organization profile validated before its own
    country parent is registered produces a permanent
    "... has no snapshot ..." failure for the rest of that process's
    lifetime, since _ensure_registered() never retries a key it already
    marked registered (confirmed empirically: a cold start that resolved
    straight to an org profile before its country parent was ever
    registered). Registering country first, for every resource_type, at
    startup removes the race entirely — country is always registered
    before any request (which could resolve straight to the org layer)
    is ever handled.

    Deliberately does NOT touch base profiles — the sidecar already ships
    every base R4 definition preloaded (confirmed via its own GET
    /profiles), so there's nothing to register there; base's own cache
    entry is left unwarmed for a future "build our own validation engine"
    consumer instead (see FhirProfileService.get_base_profile()'s
    docstring) rather than being used here.

    Deliberately does NOT touch organization profiles either — those
    stay lazy/progressive, registered the first time validate_resource()
    below actually needs one for a real request, exactly as before this
    function existed. Only the country layer needs eager startup
    treatment, since it's the one layer every organization profile's own
    baseDefinition can point at.

    Best-effort: a DB or sidecar failure here is logged, never raised —
    this is a startup warmup, not a precondition for the app to serve
    traffic. If it fails (or finds nothing, e.g. no country configured),
    the lazy per-request path in validate_resource() is still exactly the
    fallback it always was, with the same cold-start race as before for
    whichever profile didn't get warmed here."""
    country = settings.fhir_validation.country
    if not country:
        logger.info(
            "No fhir_validation.country configured — skipping country profile preload",
            extra={"event": "fhir_validation.country_preload_skipped"},
        )
        return

    from app.di.container import container

    service = container.fhir_profile.fhir_profile_service()

    try:
        total, rows = await service.list_profiles(
            resource_type=None,
            scope_level=FhirProfileScopeLevel.country,
            scope_id=country,
            status=FhirProfileStatus.active,
            limit=1000,
            offset=0,
        )
    except Exception:
        logger.exception(
            "Failed to list active country profiles for startup preload — "
            "falling back entirely to the lazy per-request registration path",
            extra={
                "event": "fhir_validation.country_preload_list_failed",
                "country": country,
            },
        )
        return

    logger.info(
        "Preloading country profiles for configured country",
        extra={
            "event": "fhir_validation.country_preload_started",
            "country": country,
            "count": total,
        },
    )

    registered = 0
    failed = 0
    for row in rows:
        resource_type = row.resource_type
        structure_definition = await service.get_country_profile(resource_type, country)
        if structure_definition is None:
            # Can't happen in practice (we just listed this exact row as
            # active) — but get_country_profile() is the cache-aside
            # source of truth other callers rely on, so trust IT, not the
            # row already in hand, and don't register something it says
            # doesn't exist.
            logger.warning(
                "Listed country profile vanished before cache warm — skipping",
                extra={
                    "event": "fhir_validation.country_preload_vanished",
                    "resource_type": resource_type,
                    "country": country,
                },
            )
            continue

        layer = _country_layer(country)
        try:
            await ensure_profile_registered(resource_type, layer, structure_definition)
        except Exception:
            failed += 1
            logger.exception(
                "Failed to register country profile with Java validator sidecar "
                "at startup — will retry lazily on the first real request for "
                "this resource_type instead",
                extra={
                    "event": "fhir_validation.country_preload_register_failed",
                    "resource_type": resource_type,
                    "country": country,
                    "url": structure_definition.get("url"),
                },
            )
            continue

        registered += 1
        logger.info(
            "Registered country profile with Java validator sidecar at startup",
            extra={
                "event": "fhir_validation.country_preload_registered",
                "resource_type": resource_type,
                "country": country,
                "url": structure_definition.get("url"),
            },
        )

    logger.info(
        "Country profile preload complete",
        extra={
            "event": "fhir_validation.country_preload_complete",
            "country": country,
            "registered": registered,
            "failed": failed,
            "total": total,
        },
    )


async def validate_resource(
    resource_type: str, fhir_resource: dict, org_id: str | None = None
) -> list[dict]:
    """Validates `fhir_resource` (true FHIR JSON) against `resource_type`'s
    most specific applicable profile, using whichever backend
    settings.fhir_validation.backend selects. Returns a list of
    {"field", "message"} dicts, empty when valid — identical shape
    regardless of backend or which layer actually fired.

    `org_id` is the caller's own tenant org_id (e.g. the verified JWT's
    activeOrganizationId for Organization/Patient/etc.) — optional, since
    not every resource_type's service has one in scope yet.

    Resolution order for "java_validator", per resource_type:
      1. If `org_id` is given AND fhir_profile has a scope_level='organization'
         row for (resource_type, org_id) — read via FhirProfileService's
         cache-aside lookup — validate against that profile's own URL. This
         is the most specific layer. No admin write path exists yet to
         create one of these rows (see FhirProfileService.get_organization_profile's
         docstring), so this lookup always misses today — it's a cheap
         negative-cached no-op — but every call site that has an org_id now
         passes it, so this starts working the moment such a row exists,
         with no further plumbing.
      2. Otherwise, if settings.fhir_validation.country is set AND
         fhir_profile has a scope_level='country' row for (resource_type,
         country) — read the same way — validate against that profile's own
         URL.
      3. Otherwise (no org/country profile found, or neither configured),
         fall back to the plain base R4 profile.

    Whichever layer actually fires, the sidecar walks baseDefinition itself
    (already confirmed for country -> base), so naming the most specific
    profile is enough — the layers underneath are never named directly here.

    "native" never considers org_id or country at all — it has no concept of
    profiles, by design (see base_r4.py's module docstring)."""
    # Payload mappers (app.fhir.mappers.<resource>.payload) build this dict
    # straight off the validated Pydantic *input* schema, which can still
    # carry non-JSON-native Python types a persisted ORM row never would —
    # Decimal (e.g. Location.position's longitude/latitude), date/datetime,
    # Enum members. jsonable_encoder() is the same conversion
    # format_response() already applies before anything ships to a client
    # (see app/core/content_negotiation.py), so validating this exact,
    # fully-JSON-safe shape keeps "what gets validated" and "what gets
    # shipped" from ever drifting apart — and avoids every backend (the
    # java_validator sidecar's httpx POST, in particular) choking on a type
    # `json.dumps`/jsonschema was never going to accept anyway.
    fhir_resource = jsonable_encoder(fhir_resource)

    if settings.fhir_validation.backend == "java_validator":
        country = settings.fhir_validation.country
        structure_definition = None
        profile_url = None
        layer = None

        if org_id:
            structure_definition = await _organization_structure_definition(
                resource_type, org_id
            )
            if structure_definition is not None:
                profile_url = structure_definition.get(
                    "url"
                ) or organization_profile_url(org_id, resource_type)
                layer = _organization_layer(org_id)

        if structure_definition is None and country:
            structure_definition = await _country_structure_definition(
                resource_type, country
            )
            if structure_definition is not None:
                profile_url = structure_definition.get(
                    "url"
                ) or country_profile_url(country, resource_type)
                layer = _country_layer(country)

        if structure_definition is None:
            if country or org_id:
                logger.info(
                    "No organization/country-layer profile for this resource type — falling back to base R4",
                    extra={
                        "event": "fhir_validation.profile_fallback",
                        "resource_type": resource_type,
                        "country": country,
                        "org_id": org_id,
                    },
                )
            profile_url = _BASE_PROFILE_URL.format(resource_type=resource_type)
            layer = None

        return await validate_via_java(
            resource_type,
            fhir_resource,
            profile_url=profile_url,
            layer=layer,
            structure_definition=structure_definition,
        )
    return validate_base_r4(resource_type, fhir_resource)

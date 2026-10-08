"""Cache-aside reads of fhir_profile, in front of FhirProfileRepository.
Cache-aside orchestration belongs here, not in the repository — see
CLAUDE.md's "Layered Architecture" (Service: thin orchestration,
Repository: all DB I/O).

Covers all three scope levels in the base -> country -> organization chain,
matching configs/cache.yaml's fhir_profile_cache design:
  - base profiles: never invalidated — no admin write path exists for them
    (seeded once from the HL7 bundle, see app/fhir_profile/seed_base_profiles.py).
  - country profiles: cached the same way, but invalidate_country_profile()
    below exists for the future super-admin edit path to call —
    evict-on-write, not update-in-place, so the next read repopulates from
    the DB instead of serving stale data.
  - organization profiles: same shape again, with its own
    invalidate_organization_profile() — no seeding or write path exists for
    this scope at all yet, so both the read and invalidate methods are
    unused today, same status get_base_profile() already had.

A cached "not found" is stored too (as JSON null), not just cache hits —
most resource_types have no country/organization profile at all today, and
without a negative cache every validation call for one of them would hit
Postgres. `cache_backend.get()` returning None means "not cached yet, ask
the DB"; a cached value that decodes to None means "confirmed: no such
profile"."""

import json

from app.core.cache.base import CacheBackend
from app.core.logging import get_logger
from app.repository.fhir_profile import FhirProfileRepository

logger = get_logger(__name__)

_BASE_KEY = "fhir_profile:base:{resource_type}"
_COUNTRY_KEY = "fhir_profile:country:{resource_type}:{country_code}"
_ORGANIZATION_KEY = "fhir_profile:organization:{resource_type}:{org_id}"


class _CoreMixin:
    def __init__(self, repository: FhirProfileRepository, cache_backend: CacheBackend):
        self.repository = repository
        self.cache_backend = cache_backend

    async def get_base_profile(self, resource_type: str) -> dict | None:
        """Returns the base layer's structure_definition dict, or None if
        this resource_type has no seeded base row. Not yet consumed by the
        validation path — java_validator.py's sidecar already has every
        base R4 definition preloaded, so there's nothing to fetch for base
        today — but ready for the next consumer (e.g. an admin "show the
        active profile" endpoint) without any further plumbing."""
        key = _BASE_KEY.format(resource_type=resource_type)
        cached = await self.cache_backend.get(key)
        if cached is not None:
            return json.loads(cached)

        profile = await self.repository.get_base(resource_type)
        structure_definition = profile.structure_definition if profile else None
        await self.cache_backend.set(key, json.dumps(structure_definition))
        return structure_definition

    async def get_country_profile(
        self, resource_type: str, country_code: str
    ) -> dict | None:
        """Returns the country layer's structure_definition dict for
        (resource_type, country_code), or None if none exists — the
        dispatch.py/java_validator.py consumer treats None the same way the
        old file-missing case worked: fall back to base R4."""
        key = _COUNTRY_KEY.format(resource_type=resource_type, country_code=country_code)
        cached = await self.cache_backend.get(key)
        if cached is not None:
            return json.loads(cached)

        profile = await self.repository.get_country(resource_type, country_code)
        structure_definition = profile.structure_definition if profile else None
        await self.cache_backend.set(key, json.dumps(structure_definition))
        return structure_definition

    async def invalidate_country_profile(
        self, resource_type: str, country_code: str
    ) -> None:
        """Call this from the future super-admin edit path, right after a
        country profile write — evicts the cache entry (whether it was
        previously a hit or a negative) so the next get_country_profile()
        call repopulates from the DB instead of serving what was cached
        before the edit. No caller exists yet — there's no admin write path
        for country profiles today — this is ready for when one is built."""
        key = _COUNTRY_KEY.format(resource_type=resource_type, country_code=country_code)
        await self.cache_backend.delete(key)
        logger.info(
            "Invalidated country profile cache entry",
            extra={
                "event": "fhir_profile_cache.country_invalidated",
                "resource_type": resource_type,
                "country_code": country_code,
            },
        )

    async def get_organization_profile(
        self, resource_type: str, org_id: str
    ) -> dict | None:
        """Returns the organization layer's structure_definition dict for
        (resource_type, org_id), or None if none exists — same cache-aside
        and negative-caching behavior as get_country_profile(). Not yet
        consumed anywhere: dispatch.py only resolves base/country today, and
        there's no seeding or admin write path for organization-scope
        profiles yet either (FhirProfileRepository.get_organization() has
        nothing to return until one exists) — this exists so the layer is
        complete end-to-end for whenever both of those are built."""
        key = _ORGANIZATION_KEY.format(resource_type=resource_type, org_id=org_id)
        cached = await self.cache_backend.get(key)
        if cached is not None:
            return json.loads(cached)

        profile = await self.repository.get_organization(resource_type, org_id)
        structure_definition = profile.structure_definition if profile else None
        await self.cache_backend.set(key, json.dumps(structure_definition))
        return structure_definition

    async def invalidate_organization_profile(
        self, resource_type: str, org_id: str
    ) -> None:
        """Same evict-on-write role as invalidate_country_profile(), for the
        future org-admin edit path. No caller exists yet."""
        key = _ORGANIZATION_KEY.format(resource_type=resource_type, org_id=org_id)
        await self.cache_backend.delete(key)
        logger.info(
            "Invalidated organization profile cache entry",
            extra={
                "event": "fhir_profile_cache.organization_invalidated",
                "resource_type": resource_type,
                "org_id": org_id,
            },
        )

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
from app.core.config import settings
from app.core.logging import get_logger
from app.errors.domain import BusinessRuleViolationError, NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.validation.java_validator import check_profile_registers
from app.models.fhir_profile.enums import FhirProfileScopeLevel, FhirProfileStatus
from app.models.fhir_profile.fhir_profile import FhirProfile
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
        key = _COUNTRY_KEY.format(
            resource_type=resource_type, country_code=country_code
        )
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
        key = _COUNTRY_KEY.format(
            resource_type=resource_type, country_code=country_code
        )
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

    # ── Write path: draft -> active -> retired ──────────────────────────
    #
    # Base profiles are never created here (seeded once from the HL7
    # bundle, see app/fhir_profile/seed_base_profiles.py). Country and
    # organization profiles go through create_profile() -> (optionally
    # update_draft_profile() while still a draft) -> activate_profile(),
    # which is the only path to status='active' and is what retires
    # whatever was active before it for the same scope — see
    # FhirProfileRepository.activate()'s own docstring for why that's one
    # atomic DB transaction rather than two separate calls from here.

    async def _resolve_parent(
        self, resource_type: str, scope_level: str
    ) -> FhirProfile | None:
        """Walks one step up the base -> country -> organization chain:
        a country profile's parent is always base; an organization
        profile's parent is the active country profile for this
        deployment's configured country (settings.fhir_validation.country)
        if that resource_type has one, else base. Goes straight to the
        repository, not get_base_profile()/get_country_profile()'s
        cache-aside dicts, because this needs the parent's own row (its id,
        for parent_profile_id — not just its structure_definition)."""
        if scope_level == FhirProfileScopeLevel.country:
            return await self.repository.get_base(resource_type)
        if scope_level == FhirProfileScopeLevel.organization:
            country = settings.fhir_validation.country
            if country:
                country_profile = await self.repository.get_country(
                    resource_type, country
                )
                if country_profile is not None:
                    return country_profile
            return await self.repository.get_base(resource_type)
        return None

    async def create_profile(
        self,
        resource_type: str,
        scope_level: str,
        scope_id: str | None,
        structure_definition: dict,
        created_by: str,
    ) -> FhirProfile:
        """Resolves this profile's parent, stamps baseDefinition/derivation
        onto `structure_definition` to match (overwriting whatever the
        caller sent — the chain is enforced by this service, not trusted
        from the request), runs it past the sidecar's best-effort
        registration check, and persists it as status='draft' if that
        check raises nothing. Raises BusinessRuleViolationError (one of
        this codebase's existing 422s) for a scope_level this write path
        doesn't support or a missing scope_id, FhirValidationError (422,
        same shape every other FHIR validation failure uses) if the
        sidecar objects — see check_profile_registers()'s own docstring
        for what that check does and doesn't guarantee."""
        if scope_level == FhirProfileScopeLevel.base:
            raise BusinessRuleViolationError(
                "Base profiles come from the HL7 bundle seed, not this endpoint."
            )
        if not scope_id:
            raise BusinessRuleViolationError(
                f"scope_id is required for a {scope_level} profile."
            )

        parent = await self._resolve_parent(resource_type, scope_level)
        if parent is None:
            raise BusinessRuleViolationError(
                f"No base profile exists yet for resource_type={resource_type!r} "
                "— seed one before creating a country/organization profile for it."
            )

        candidate = dict(structure_definition)
        candidate["baseDefinition"] = parent.canonical_url
        candidate.setdefault("derivation", "constraint")
        candidate.setdefault("type", resource_type)
        canonical_url = candidate.get("url")
        if not canonical_url:
            raise BusinessRuleViolationError("structure_definition.url is required.")

        errors = await check_profile_registers(candidate)
        if errors:
            logger.warning(
                "Candidate profile rejected by validator sidecar",
                extra={
                    "event": "fhir_profile.registration_rejected",
                    "resource_type": resource_type,
                    "scope_level": scope_level,
                    "scope_id": scope_id,
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

        profile = await self.repository.create_profile(
            resource_type=resource_type,
            scope_level=scope_level,
            scope_id=scope_id,
            canonical_url=canonical_url,
            version=str(candidate.get("version", "1")),
            structure_definition=candidate,
            parent_profile_id=parent.id,
            created_by=created_by,
        )
        logger.info(
            "FHIR profile created as draft",
            extra={
                "event": "fhir_profile.created",
                "profile_id": profile.id,
                "resource_type": resource_type,
                "scope_level": scope_level,
                "scope_id": scope_id,
                "parent_profile_id": parent.id,
            },
        )
        return profile

    async def get_profile(self, profile_id: int) -> FhirProfile:
        profile = await self.repository.get_by_id(profile_id)
        if profile is None:
            raise NotFoundError("FHIR profile not found")
        return profile

    async def list_profiles(
        self,
        resource_type: str | None = None,
        scope_level: str | None = None,
        scope_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[int, list[FhirProfile]]:
        return await self.repository.list_profiles(
            resource_type, scope_level, scope_id, status, limit, offset
        )

    async def update_draft_profile(
        self, profile_id: int, structure_definition: dict, updated_by: str
    ) -> FhirProfile:
        """Only a status='draft' row can be edited — an active or retired
        profile is immutable history; create a new version instead. Re-runs
        the same sidecar check create_profile() does, since the edit could
        just as easily introduce whatever that check does catch."""
        profile = await self.repository.get_by_id(profile_id)
        if profile is None:
            raise NotFoundError("FHIR profile not found")
        if profile.status != FhirProfileStatus.draft:
            raise BusinessRuleViolationError(
                f"Only a draft profile can be edited (this one is {profile.status})."
            )

        candidate = dict(structure_definition)
        candidate["baseDefinition"] = profile.structure_definition.get("baseDefinition")
        candidate.setdefault("derivation", "constraint")
        candidate.setdefault("type", profile.resource_type)
        candidate.setdefault("url", profile.canonical_url)

        errors = await check_profile_registers(candidate)
        if errors:
            raise FhirValidationError(errors)

        updated = await self.repository.update_draft(profile_id, candidate, updated_by)
        logger.info(
            "FHIR profile draft updated",
            extra={"event": "fhir_profile.draft_updated", "profile_id": profile_id},
        )
        return updated

    async def activate_profile(self, profile_id: int, updated_by: str) -> FhirProfile:
        """The only path to status='active'. Retires whatever was
        previously active for the same (resource_type, scope_level,
        scope_id) as one atomic DB transaction (see
        FhirProfileRepository.activate()), then evicts the matching cache
        entry so the next validation call re-reads from the DB instead of
        serving what was cached before this activation."""
        profile = await self.repository.get_by_id(profile_id)
        if profile is None:
            raise NotFoundError("FHIR profile not found")
        if profile.status == FhirProfileStatus.active:
            return profile
        if profile.status == FhirProfileStatus.retired:
            raise BusinessRuleViolationError(
                "A retired profile can't be reactivated directly — create a new version instead."
            )

        activated = await self.repository.activate(profile_id, updated_by)
        if activated.scope_level == FhirProfileScopeLevel.country:
            await self.invalidate_country_profile(
                activated.resource_type, activated.scope_id
            )
        elif activated.scope_level == FhirProfileScopeLevel.organization:
            await self.invalidate_organization_profile(
                activated.resource_type, activated.scope_id
            )
        logger.info(
            "FHIR profile activated",
            extra={
                "event": "fhir_profile.activated",
                "profile_id": profile_id,
                "resource_type": activated.resource_type,
                "scope_level": activated.scope_level,
                "scope_id": activated.scope_id,
            },
        )
        return activated

    async def delete_profile(self, profile_id: int) -> None:
        """Refuses to delete a status='active' row — activate a
        replacement first, which retires this one as part of that same
        transaction, rather than leaving a scope with zero active profiles
        (silently falling back one layer, which could surprise whoever
        thought this org/country still had its own profile enforced)."""
        profile = await self.repository.get_by_id(profile_id)
        if profile is None:
            raise NotFoundError("FHIR profile not found")
        if profile.status == FhirProfileStatus.active:
            raise BusinessRuleViolationError(
                "Cannot delete an active profile — activate a replacement first."
            )
        await self.repository.delete_profile(profile_id)
        logger.info(
            "FHIR profile deleted",
            extra={"event": "fhir_profile.deleted", "profile_id": profile_id},
        )

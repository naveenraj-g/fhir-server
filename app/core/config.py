from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class AppConfig(BaseModel):
    """FastAPI app metadata + interactive-docs exposure."""

    title: str = "FHIR Server"
    version: str = "1.0.0"

    # Gates only the interactive /docs (Swagger) and /redoc UIs. /openapi.json
    # itself is never gated by this — it's the FastMCP contract (see
    # CLAUDE.md's "OpenAPI Spec = MCP Contract"), so it must stay reachable
    # regardless of whether the human-facing UI is turned off.
    docs_enabled: bool = True


class CorsConfig(BaseModel):
    """No CORSMiddleware is registered at all while `enabled` is false (the
    default) — this server has historically had no browser-facing callers.
    Turn on and fill in `allow_origins` the moment one exists; never use
    `allow_origins: ["*"]` together with `allow_credentials: true` — browsers
    reject that combination outright."""

    enabled: bool = False
    allow_origins: list[str] = Field(default_factory=list)
    allow_credentials: bool = False
    allow_methods: list[str] = Field(default_factory=lambda: ["*"])
    allow_headers: list[str] = Field(default_factory=lambda: ["*"])

    @model_validator(mode="after")
    def _reject_wildcard_with_credentials(self) -> "CorsConfig":
        if self.allow_credentials and "*" in self.allow_origins:
            raise ValueError(
                "cors.allow_credentials cannot be true while cors.allow_origins "
                "includes '*' — browsers reject that combination outright. "
                "List explicit origins instead."
            )
        return self


class AuthConfig(BaseModel):
    # Algorithms PyJWT will accept when verifying a token's signature (see
    # app/auth/dependencies.py's decode_token). Must match whatever the IAM
    # (IAM_JWKS_URL/IAM_ISSUER) actually signs with.
    algorithms: list[str] = Field(default_factory=lambda: ["EdDSA", "RS256"])


class DatabaseConfig(BaseModel):
    """SQLAlchemy async engine pool sizing — see app/core/database.py's
    Database.__init__. Defaults match SQLAlchemy's own (pool_size=5,
    max_overflow=10) except pool_pre_ping, which we turn on: without it a
    connection that Postgres or a proxy silently dropped surfaces as a
    mid-request error instead of being caught and replaced at checkout."""

    pool_size: int = 5
    max_overflow: int = 10
    pool_pre_ping: bool = True
    pool_recycle: int = 1800


class RedisConfig(BaseModel):
    """Global Redis on/off switch.

    `enabled: false` forces every Redis-backed dependent (rate limiting,
    FHIR profile caching, anything Redis-backed added later) to its
    non-Redis fallback — see Settings._apply_redis_switch() below —
    regardless of what that dependent's own backend field says. `enabled:
    true` defers to each dependent's own setting instead.
    """

    enabled: bool = True


class RateLimitConfig(BaseModel):
    # "redis" (coordinated across instances) or "memory" (per-process, no
    # cross-instance coordination). Only consulted when the global
    # `redis.enabled` switch above is true — forced to "memory" otherwise.
    backend: Literal["redis", "memory"] = "redis"
    read_limit: int = 100
    write_limit: int = 20
    window_seconds: int = 60


class FhirProfileCacheConfig(BaseModel):
    """Caches `fhir_profile` DB rows (app/models/fhir_profile/) so validation
    doesn't hit Postgres on every request. Covers all three scope levels in
    the base -> country -> organization chain (app/services/fhir_profile_service.py):
    base profiles (immutable — no admin write path exists for them, see
    app/fhir/profiling/README.md — so once cached, never invalidated), and
    country/organization profiles (evict on write once each one's admin
    edit path exists — FhirProfileService already has both
    invalidate_country_profile() and invalidate_organization_profile()
    ready, just no caller yet — let the next read repopulate from the DB
    rather than updating the cache in place).

    "redis" (shared across instances) or "memory" (per-process). Only
    consulted when the global `redis.enabled` switch above is true — forced
    to "memory" otherwise, same as rate_limit.backend.
    """

    backend: Literal["redis", "memory"] = "redis"


class PaginationConfig(BaseModel):
    """Defaults for the shared `ListParams` dependency (app/core/pagination.py)
    used by every list endpoint across the eight JWT/RBAC-rolled-out
    resources (Patient, Practitioner, Organization, Location,
    HealthcareService, PractitionerRole, Schedule, Slot) — the only routers
    that share one `ListParams` class instead of declaring `limit`/`offset`
    inline per route."""

    default_limit: int = 50
    max_limit: int = 200


class RoutesConfig(BaseModel):
    # Which FHIR resource routers get mounted under /api/fhir/v1 at startup —
    # see app.routers.discover_routers() and CLAUDE.md's
    # "Enabling/Disabling Resources" section. Not listed = not mounted.
    enabled: list[str] = Field(default_factory=list)


class JavaValidatorConfig(BaseModel):
    """Connection details for the stopgap HL7 Java FHIR validator sidecar
    (docker/fhir-validator/) — see
    docs/structure-definitions/12-three-layer-validation-architecture.md.
    base_url defaults to the host-mapped port docker-compose.dev.yml exposes
    (the API runs on the host, the validator runs in Docker); override via
    FHIR_VALIDATION__JAVA_VALIDATOR__BASE_URL for docker-compose.yml/
    docker-compose.prod.yml, where it's reachable by service name
    ("http://fhir-validator:4567") instead."""

    base_url: str = "http://localhost:4567"
    timeout_seconds: float = 30.0


class FhirValidationConfig(BaseModel):
    """Selects which engine validates a resource against base R4 (and, once
    built, country/organization profiles) — see
    docs/structure-definitions/12-three-layer-validation-architecture.md.

    "native": this project's own fhir.schema.json + jsonschema structural
    check (app/fhir/validation/base_r4.py) — fast, in-process, but
    structural-only (no invariants, so org-1/org-2/org-3 aren't enforced).
    This is the default so existing behavior/tests don't change underneath
    anyone.

    "java_validator": delegates to the HL7 Java validator sidecar instead —
    slower (a network call per validation), but checks real invariants too.
    Swapping is this one field; no caller of app.fhir.validation needs to
    know which backend is active."""

    # Which country-layer profile to apply, on top of base R4 — e.g. "IN".
    # null/omitted means base R4 only, same as before country profiles
    # existed. A single, global, deploy-time choice (see dispatch.py's
    # module docstring for why this is deliberately NOT resolved per-request
    # or per-tenant): one deployment serves one country, same as a specific
    # hospital's instance or a single-country SaaS rollout would — swapping
    # country is one config edit + redeploy, not a runtime lookup. Only
    # consulted when backend is "java_validator"; "native" has no concept of
    # profiles at all. Only takes effect for a resource_type that actually
    # has an `app/fhir/profiling/<resource_type>/country_<code>.json` file —
    # falls back to base R4 for any resource_type that doesn't yet.
    country: str | None = None

    backend: Literal["native", "java_validator"] = "native"
    java_validator: JavaValidatorConfig = Field(default_factory=JavaValidatorConfig)


class LogConfig(BaseModel):
    """Observability config — consumed by app.core.logging.setup_logging(),
    app.middleware.access_log, and app.core.database's query listeners.
    See CLAUDE.md's "Logging & Observability" section."""

    # Root log level. DEBUG turns on the per-layer flow logging that services
    # and repositories emit; INFO keeps only business outcomes + the access log.
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # "json" (one JSON object per line — what log aggregators want) or
    # "console" (flat, human-readable; local development only).
    format: Literal["json", "console"] = "json"

    # Both of the above are matched case-insensitively: `format: JSON` and
    # `level: debug` are as valid as the canonical spellings. Without this a
    # perfectly reasonable edit to configs/config.yaml crashes the app at
    # import time with a pydantic literal_error, which is a miserable first
    # experience — and these two are the settings people actually hand-edit.
    @field_validator("level", "format", mode="before")
    @classmethod
    def _normalise_case(cls, v):
        if isinstance(v, str):
            return v.upper() if v.upper() in _LOG_LEVELS else v.lower()
        return v

    # ⚠️ PHI. Logs full request payloads at DEBUG via log_payload(). This is a
    # FHIR server — enabling it writes patient names, addresses, birth dates
    # and identifiers into the log stream. Local development only; `redact`
    # below is a backstop for obvious secrets, NOT a PHI safeguard.
    debug_payloads: bool = False

    # Any SQL statement slower than this logs a `db.slow_query` WARNING.
    slow_query_ms: int = 500

    # Log every SQL statement at DEBUG (very noisy — debugging only).
    sql_echo: bool = False

    # Re-enable Uvicorn's own per-request access line
    # (`INFO: 127.0.0.1:53412 - "GET /patients/ HTTP/1.1" 200 OK`).
    #
    # Off by default for two reasons: it duplicates app.middleware.access_log's
    # richer `http.request` line, and — because the `uvicorn.access` logger sets
    # propagate=False and keeps its own handler — it bypasses our formatter and
    # emits PLAIN TEXT even when format is "json", which breaks any tool
    # parsing the stream. Turn it on to see both effects for yourself.
    uvicorn_access: bool = False

    # Field names masked by log_payload() even when debug_payloads is on.
    # Matched case-insensitively against dict keys at any nesting depth.
    redact: list[str] = Field(
        default_factory=lambda: ["authorization", "token", "password", "secret"]
    )


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    FHIR_DATABASE_URL: str
    # Optional — only required when redis.enabled is true (the default).
    # Deployments that run with redis.enabled: false need not set this.
    REDIS_URL: str | None = None

    # BetterAuth / IAM — used by app.auth to verify JWTs via JWKS.
    IAM_JWKS_URL: str
    IAM_ISSUER: str

    app: AppConfig = Field(default_factory=AppConfig)
    cors: CorsConfig = Field(default_factory=CorsConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    fhir_profile_cache: FhirProfileCacheConfig = Field(default_factory=FhirProfileCacheConfig)
    pagination: PaginationConfig = Field(default_factory=PaginationConfig)
    routes: RoutesConfig = Field(default_factory=RoutesConfig)
    fhir_validation: FhirValidationConfig = Field(default_factory=FhirValidationConfig)
    logging: LogConfig = Field(default_factory=LogConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        # .env carries a few docker-compose-only keys (POSTGRES_USER/
        # PASSWORD/DB/PORT) that FHIR_DATABASE_URL's DSN already encodes in
        # full — nothing in Settings declares them individually, so they'd
        # otherwise fail as unknown fields.
        extra="ignore",
    )

    @model_validator(mode="after")
    def _apply_redis_switch(self) -> "Settings":
        """When Redis is globally disabled, force every dependent's backend
        to its non-Redis fallback here — once — so nothing downstream
        (middleware, DI, etc.) needs to know the global switch exists; it
        just reads its own already-resolved backend field."""
        if not self.redis.enabled:
            self.rate_limit.backend = "memory"
            self.fhir_profile_cache.backend = "memory"
        return self

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Precedence, highest first: real env var > `.env` >
        `configs/config.yaml` + `configs/cache.yaml` > field defaults. `.env`
        stays reserved for true per-environment secrets (DB/Redis/IAM URLs);
        everything else — rate limiting, which routes are enabled, caching —
        is checked-in application behavior that lives in those two YAML
        files instead. They're two peer sources at the same precedence tier,
        not a fallback chain between them: config.yaml carries general
        app-behavior settings, including both the global `redis` on/off
        switch (Redis also backs sessions and get_redis(), not just
        caching, so whether it's available at all is an infra-level
        decision) and `rate_limit` (Redis-backed, but not a cache itself —
        a shared sliding-window counter, not something stored to avoid a
        re-fetch). cache.yaml carries only genuine caching settings
        (`fhir_profile_cache` today — see that file's header comment).
        Their top-level keys never overlap, so load order between the two
        doesn't matter.

        A future secrets-manager source (e.g. AWS Secrets Manager/SSM) would
        slot into this same tuple as another `PydanticBaseSettingsSource`,
        ranked between `env_settings` and `dotenv_settings` — no changes
        needed anywhere else, since consumers only ever read `settings.*`.
        """
        # yaml_file_encoding is explicit because the source otherwise opens the
        # file with the platform default — cp1252 on Windows, which blows up on
        # any non-ASCII byte in the committed config (e.g. the ⚠️ in the
        # debug_payloads PHI warning).
        yaml_settings = YamlConfigSettingsSource(
            settings_cls,
            yaml_file="configs/config.yaml",
            yaml_file_encoding="utf-8",
        )
        cache_yaml_settings = YamlConfigSettingsSource(
            settings_cls,
            yaml_file="configs/cache.yaml",
            yaml_file_encoding="utf-8",
        )
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            yaml_settings,
            cache_yaml_settings,
            file_secret_settings,
        )


settings = Settings()

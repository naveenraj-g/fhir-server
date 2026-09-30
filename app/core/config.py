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

    `enabled: false` forces every Redis-backed dependent (rate limiting
    today, anything Redis-backed added later) to its non-Redis fallback —
    see Settings._apply_redis_switch() below — regardless of what that
    dependent's own backend field says. `enabled: true` defers to each
    dependent's own setting instead.
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
    pagination: PaginationConfig = Field(default_factory=PaginationConfig)
    routes: RoutesConfig = Field(default_factory=RoutesConfig)
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
        `configs/config.yaml` > field defaults. `.env` stays reserved for
        true per-environment secrets (DB/Redis/IAM URLs); everything else —
        rate limiting, which routes are enabled — is checked-in application
        behavior that lives in `configs/config.yaml` instead.

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
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            yaml_settings,
            file_secret_settings,
        )


settings = Settings()

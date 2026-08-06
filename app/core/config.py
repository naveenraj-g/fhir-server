from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class RateLimitConfig(BaseModel):
    # "redis" (coordinated across instances) or "memory" (per-process, no
    # cross-instance coordination). Redis remains required regardless — this
    # only selects the rate limiter's counting backend.
    backend: Literal["redis", "memory"] = "redis"
    read_limit: int = 100
    write_limit: int = 20
    window_seconds: int = 60


class RoutesConfig(BaseModel):
    # Which FHIR resource routers get mounted under /api/fhir/v1 at startup —
    # see app.routers.discover_routers() and CLAUDE.md's
    # "Enabling/Disabling Resources" section. Not listed = not mounted.
    enabled: list[str] = Field(default_factory=list)


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    FHIR_DATABASE_URL: str
    REDIS_URL: str

    # BetterAuth / IAM — used by app.auth to verify JWTs via JWKS.
    IAM_JWKS_URL: str
    IAM_ISSUER: str

    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    routes: RoutesConfig = Field(default_factory=RoutesConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

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
        yaml_settings = YamlConfigSettingsSource(
            settings_cls, yaml_file="configs/config.yaml"
        )
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            yaml_settings,
            file_secret_settings,
        )


settings = Settings()

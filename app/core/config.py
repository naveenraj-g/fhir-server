from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    FHIR_DATABASE_URL: str
    REDIS_URL: str

    # BetterAuth / IAM — used by app.auth to verify JWTs via JWKS.
    IAM_JWKS_URL: str
    IAM_ISSUER: str

    # Rate-limiter backend: "redis" (coordinated across instances) or
    # "memory" (per-process, no cross-instance coordination). Redis remains
    # required regardless — this only selects the rate limiter's backend.
    RATE_LIMIT_BACKEND: Literal["redis", "memory"] = "redis"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()

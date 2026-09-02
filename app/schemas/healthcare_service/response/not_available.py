from pydantic import BaseModel, Field

from app.schemas.common.fhir import FHIRPeriod

from ._shared import _AuditFields


class FHIRHealthcareServiceNotAvailable(BaseModel):
    """HealthcareService.notAvailable — FHIR camelCase BackboneElement."""

    description: str | None = Field(
        None,
        description="The reason presented to the user as to why this time is not available.",
    )
    during: FHIRPeriod | None = Field(
        None, description="Service is not available during this period."
    )


class PlainHealthcareServiceNotAvailable(_AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    description: str | None = Field(
        None,
        description="The reason presented to the user as to why this time is not available.",
    )
    during_start: str | None = Field(
        None,
        description="Start of the period of time that this service is not available.",
    )
    during_end: str | None = Field(
        None,
        description="End of the period of time that this service is not available.",
    )

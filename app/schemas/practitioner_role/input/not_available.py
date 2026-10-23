from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PractitionerRoleNotAvailableInput(BaseModel):
    """PractitionerRole.notAvailable — the practitioner is not available at
    this role/location during this period, for the given reason
    (BackboneElement)."""

    model_config = ConfigDict(extra="forbid")
    description: str = Field(
        ...,
        description="The reason that can be presented to the user as to why this time is not available (required).",
    )
    during_start: datetime | None = Field(
        None,
        description="Start of the period of time that this practitioner is not available.",
    )
    during_end: datetime | None = Field(
        None,
        description="End of the period of time that this practitioner is not available.",
    )

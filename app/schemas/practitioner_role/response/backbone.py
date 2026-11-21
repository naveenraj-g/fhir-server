from pydantic import BaseModel, Field

from app.schemas.datatypes import FHIRPeriod


class FHIRPractitionerRoleAvailableTime(BaseModel):
    """PractitionerRole.availableTime — times the practitioner is available."""

    daysOfWeek: list[str] | None = Field(
        None, description="mon | tue | wed | thu | fri | sat | sun."
    )
    allDay: bool | None = Field(
        None, description="Always available (e.g. 24 hour service)."
    )
    availableStartTime: str | None = Field(
        None, description="Opening time of day (hh:mm:ss)."
    )
    availableEndTime: str | None = Field(
        None, description="Closing time of day (hh:mm:ss)."
    )


class FHIRPractitionerRoleNotAvailable(BaseModel):
    """PractitionerRole.notAvailable — not available during this time."""

    description: str = Field(
        ...,
        description="Reason presented to the user explaining why the practitioner is not available.",
    )
    during: FHIRPeriod | None = Field(
        None, description="Service not available from this date."
    )

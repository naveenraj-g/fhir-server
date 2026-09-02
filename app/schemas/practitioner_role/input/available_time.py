from datetime import time

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import PractitionerRoleDayOfWeek


class PractitionerRoleAvailableTimeInput(BaseModel):
    """PractitionerRole.availableTime — times the role is available (BackboneElement)."""

    model_config = ConfigDict(extra="forbid")
    days_of_week: list[PractitionerRoleDayOfWeek] | None = Field(
        None,
        description="Indicates which days of the week are available between the start/end times, e.g. ['mon', 'wed', 'fri'].",
    )
    all_day: bool | None = Field(
        None,
        description="Is this always available (hence times are irrelevant)? e.g. 24 hour service.",
    )
    available_start_time: time | None = Field(
        None, description="The opening time, in HH:MM:SS format."
    )
    available_end_time: time | None = Field(
        None, description="The closing time, in HH:MM:SS format."
    )

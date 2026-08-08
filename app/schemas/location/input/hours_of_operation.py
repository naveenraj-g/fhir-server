from datetime import time

from pydantic import BaseModel, ConfigDict, Field

from app.models.location.enums import LocationDayOfWeek


class LocationHoursOfOperationInput(BaseModel):
    """Location.hoursOfOperation — what days/times during a week the location
    is generally open (BackboneElement).

    `days_of_week` is a real list here even though the column stores it
    comma-separated (see LocationHoursOfOperation's docstring) — the repository
    joins on write and the mapper splits on read, so the API surface stays a
    proper FHIR `daysOfWeek[]`.
    """

    model_config = ConfigDict(extra="forbid")
    days_of_week: list[LocationDayOfWeek] | None = Field(
        None,
        description="Indicates which days of the week are available between the start and end times — mon|tue|wed|thu|fri|sat|sun.",
    )
    all_day: bool | None = Field(
        None, description="The Location is open all day (24 hours)."
    )
    opening_time: time | None = Field(
        None,
        description="Time that the Location opens, as a wall-clock time with no date and no timezone (e.g. '09:00:00').",
    )
    closing_time: time | None = Field(
        None,
        description="Time that the Location closes, as a wall-clock time with no date and no timezone (e.g. '17:30:00').",
    )

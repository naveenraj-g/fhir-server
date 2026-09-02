from pydantic import BaseModel, Field

from ._shared import _AuditFields


class FHIRHealthcareServiceAvailableTime(BaseModel):
    """HealthcareService.availableTime — FHIR camelCase BackboneElement."""

    daysOfWeek: list[str] | None = Field(
        None, description="mon|tue|wed|thu|fri|sat|sun."
    )
    allDay: bool | None = Field(
        None, description="Is this always available (hence times are irrelevant)?"
    )
    availableStartTime: str | None = Field(
        None, description="The opening time, HH:MM:SS."
    )
    availableEndTime: str | None = Field(
        None, description="The closing time, HH:MM:SS."
    )


class PlainHealthcareServiceAvailableTime(_AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    days_of_week: list[str] | None = Field(
        None, description="Days of the week available between the start/end times."
    )
    all_day: bool | None = Field(
        None, description="Is this always available (hence times are irrelevant)?"
    )
    available_start_time: str | None = Field(
        None, description="The opening time, HH:MM:SS."
    )
    available_end_time: str | None = Field(
        None, description="The closing time, HH:MM:SS."
    )

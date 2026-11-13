"""Location's own BackboneElements, FHIR R4-shaped
(https://www.hl7.org/fhir/R4/location.html)."""

from decimal import Decimal
from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import FhirInputModel

DayOfWeek = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class LocationPositionInput(FhirInputModel):
    """Location.position — WGS84 coordinates. longitude and latitude are
    both required (1..1) within position; this is what the `near` search
    parameter measures distance from."""

    longitude: Decimal = Field(..., description="Longitude with WGS84 datum.")
    latitude: Decimal = Field(..., description="Latitude with WGS84 datum.")
    altitude: Decimal | None = Field(None, description="Altitude with WGS84 datum.")


class LocationHoursOfOperationInput(FhirInputModel):
    """Location.hoursOfOperation — what days/times the location is usually open."""

    daysOfWeek: list[DayOfWeek] | None = Field(
        None, description="mon | tue | wed | thu | fri | sat | sun (required binding DaysOfWeek)."
    )
    allDay: bool | None = Field(None, description="The location is open all day.")
    openingTime: str | None = Field(None, description="Time the location opens (hh:mm:ss).")
    closingTime: str | None = Field(None, description="Time the location closes (hh:mm:ss).")

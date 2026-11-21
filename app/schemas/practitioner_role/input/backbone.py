"""PractitionerRole's own BackboneElements, FHIR R4-shaped
(https://www.hl7.org/fhir/R4/practitionerrole.html). Every other element is a
shared FHIR datatype from app.schemas.fhir_input."""

from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import FhirInputModel, FhirPeriodInput

DayOfWeek = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class PractitionerRoleAvailableTimeInput(FhirInputModel):
    """PractitionerRole.availableTime — times the practitioner is available
    at this role."""

    daysOfWeek: list[DayOfWeek] | None = Field(
        None,
        description="mon | tue | wed | thu | fri | sat | sun (required binding DaysOfWeek).",
    )
    allDay: bool | None = Field(
        None, description="Always available (e.g. 24 hour service)."
    )
    availableStartTime: str | None = Field(
        None, description="Opening time of day (hh:mm:ss); ignored if allDay = true."
    )
    availableEndTime: str | None = Field(
        None, description="Closing time of day (hh:mm:ss); ignored if allDay = true."
    )


class PractitionerRoleNotAvailableInput(FhirInputModel):
    """PractitionerRole.notAvailable — not available during this time due to
    the provided reason."""

    description: str = Field(
        ...,
        description="Reason presented to the user explaining why the practitioner is not available (required by R4).",
    )
    during: FhirPeriodInput | None = Field(
        None, description="Service not available from this date."
    )

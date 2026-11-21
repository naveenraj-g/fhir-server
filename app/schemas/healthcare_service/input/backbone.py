"""HealthcareService's own BackboneElements, FHIR R4-shaped
(https://www.hl7.org/fhir/R4/healthcareservice.html). Every other element is
a shared FHIR datatype from app.schemas.fhir_input."""

from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirInputModel,
    FhirPeriodInput,
)

DayOfWeek = Literal["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class HealthcareServiceEligibilityInput(FhirInputModel):
    """HealthcareService.eligibility — specific eligibility requirements
    required to use the service."""

    code: FhirCodeableConceptInput | None = Field(
        None, description="Coded value for the eligibility."
    )
    comment: str | None = Field(
        None,
        description="Describes the eligibility conditions for the service (markdown).",
    )


class HealthcareServiceAvailableTimeInput(FhirInputModel):
    """HealthcareService.availableTime — times the service is conducted."""

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


class HealthcareServiceNotAvailableInput(FhirInputModel):
    """HealthcareService.notAvailable — not available during this time due
    to provided reason."""

    description: str = Field(
        ...,
        description="Reason presented to the user explaining why the service is not available (required by R4).",
    )
    during: FhirPeriodInput | None = Field(
        None, description="Service not available from this date."
    )

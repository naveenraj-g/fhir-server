from pydantic import BaseModel, Field

from app.schemas.datatypes import FHIRCodeableConcept, FHIRPeriod


class FHIRHealthcareServiceEligibility(BaseModel):
    """HealthcareService.eligibility — specific eligibility requirements."""

    code: FHIRCodeableConcept | None = Field(
        None, description="Coded value for the eligibility."
    )
    comment: str | None = Field(
        None, description="Describes the eligibility conditions for the service."
    )


class FHIRHealthcareServiceAvailableTime(BaseModel):
    """HealthcareService.availableTime — times the service is conducted."""

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


class FHIRHealthcareServiceNotAvailable(BaseModel):
    """HealthcareService.notAvailable — not available during this time."""

    description: str = Field(
        ...,
        description="Reason presented to the user explaining why the service is not available.",
    )
    during: FHIRPeriod | None = Field(
        None, description="Service not available from this date."
    )

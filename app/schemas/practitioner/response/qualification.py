from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRPeriod,
    FHIRReference,
)


class FHIRPractitionerQualification(BaseModel):
    """Practitioner.qualification — certification, licenses, or training
    pertaining to the provision of care."""

    identifier: list[FHIRIdentifier] | None = Field(
        None, description="An identifier for this qualification for the practitioner."
    )
    code: FHIRCodeableConcept = Field(
        ..., description="Coded representation of the qualification."
    )
    period: FHIRPeriod | None = Field(
        None, description="Period during which the qualification is valid."
    )
    issuer: FHIRReference | None = Field(
        None, description="Organization that regulates and issues the qualification."
    )

from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRAddress,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRHumanName,
    FHIRPeriod,
    FHIRReference,
)


class FHIRPatientContact(BaseModel):
    """Patient.contact — a contact party for the patient."""

    relationship: list[FHIRCodeableConcept] | None = Field(None, description="The kind of relationship.")
    name: FHIRHumanName | None = Field(None, description="A name associated with the contact person.")
    telecom: list[FHIRContactPoint] | None = Field(None, description="A contact detail for the person.")
    address: FHIRAddress | None = Field(None, description="Address for the contact person.")
    gender: str | None = Field(None, description="male | female | other | unknown.")
    organization: FHIRReference | None = Field(None, description="Organization that is associated with the contact.")
    period: FHIRPeriod | None = Field(None, description="The period during which this contact is valid.")

from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRAddress,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRHumanName,
)


class FHIROrganizationContact(BaseModel):
    """Organization.contact — contact for the organization for a certain purpose."""

    purpose: FHIRCodeableConcept | None = Field(
        None, description="Indicates a purpose for which the contact can be reached."
    )
    name: FHIRHumanName | None = Field(
        None, description="A name associated with the contact."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None,
        description="A contact detail (e.g. a telephone number or an email address) by which the party may be contacted.",
    )
    address: FHIRAddress | None = Field(
        None, description="Visiting or postal addresses for the contact."
    )

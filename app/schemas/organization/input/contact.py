from pydantic import Field

from app.schemas.fhir_input import (
    FhirAddressInput,
    FhirCodeableConceptInput,
    FhirContactPointInput,
    FhirHumanNameInput,
    FhirInputModel,
)


class OrganizationContactInput(FhirInputModel):
    """Organization.contact — contact for the organization for a certain
    purpose (BackboneElement). The only Organization-specific input type:
    every other element is a shared FHIR datatype from app.schemas.fhir_input."""

    purpose: FhirCodeableConceptInput | None = Field(
        None,
        description="The type of contact — e.g. ADMIN, BILL, HR, PAYOR, PATINF, PRESS.",
    )
    name: FhirHumanNameInput | None = Field(
        None, description="A name associated with the contact."
    )
    telecom: list[FhirContactPointInput] | None = Field(
        None,
        description="Contact details (telephone, email, etc.) for a contact.",
    )
    address: FhirAddressInput | None = Field(
        None, description="Visiting or postal addresses for the contact."
    )

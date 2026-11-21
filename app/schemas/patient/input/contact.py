from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirAddressInput,
    FhirCodeableConceptInput,
    FhirContactPointInput,
    FhirHumanNameInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)


class PatientContactInput(FhirInputModel):
    """Patient.contact — a contact party (e.g. guardian, partner, friend) for
    the patient (BackboneElement). R4 requires at least one of name, telecom,
    address or organization."""

    relationship: list[FhirCodeableConceptInput] | None = Field(
        None, description="The kind of relationship."
    )
    name: FhirHumanNameInput | None = Field(
        None, description="A name associated with the contact person."
    )
    telecom: list[FhirContactPointInput] | None = Field(
        None,
        description="A contact detail for the person, e.g. a telephone number or an email address.",
    )
    address: FhirAddressInput | None = Field(
        None, description="Address for the contact person."
    )
    gender: Literal["male", "female", "other", "unknown"] | None = Field(
        None, description="male | female | other | unknown."
    )
    organization: FhirReferenceInput | None = Field(
        None,
        description="Organization that is associated with the contact — Reference(Organization). A relative 'Organization/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    period: FhirPeriodInput | None = Field(
        None,
        description="The period during which this contact person or organization is valid to be contacted.",
    )

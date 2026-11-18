from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)


class PractitionerQualificationInput(FhirInputModel):
    """Practitioner.qualification — certification, licenses, or training
    pertaining to the provision of care (BackboneElement). The only
    Practitioner-specific input type: every other element is a shared FHIR
    datatype from app.schemas.fhir_input."""

    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="An identifier for this qualification for the practitioner."
    )
    code: FhirCodeableConceptInput = Field(
        ..., description="Coded representation of the qualification (required by R4)."
    )
    period: FhirPeriodInput | None = Field(
        None, description="Period during which the qualification is valid."
    )
    issuer: FhirReferenceInput | None = Field(
        None,
        description="Organization that regulates and issues the qualification — Reference(Organization). A relative 'Organization/<id>' reference must exist in the caller's org (422 otherwise).",
    )

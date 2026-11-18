from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import FhirInputModel, FhirReferenceInput


class PatientLinkInput(FhirInputModel):
    """Patient.link — a link to another patient or related-person resource that
    concerns the same actual person (BackboneElement)."""

    other: FhirReferenceInput = Field(
        ...,
        description="The other patient or related person resource that the link refers to — Reference(Patient | RelatedPerson), required by R4. A relative 'Patient/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    type: Literal["replaced-by", "replaces", "refer", "seealso"] = Field(
        ..., description="replaced-by | replaces | refer | seealso (required by R4)."
    )

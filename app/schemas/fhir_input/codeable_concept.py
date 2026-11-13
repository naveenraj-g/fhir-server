from pydantic import Field

from app.schemas.fhir_input.base import FhirInputModel
from app.schemas.fhir_input.coding import FhirCodingInput


class FhirCodeableConceptInput(FhirInputModel):
    """FHIR R4 CodeableConcept — one or more codings plus a text representation."""

    coding: list[FhirCodingInput] | None = Field(
        None, description="Code(s) defined by a terminology system for this concept."
    )
    text: str | None = Field(
        None,
        description="A human language representation of the concept as seen/selected/entered by the user.",
    )


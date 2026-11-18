from pydantic import Field

from app.schemas.fhir_input import FhirCodeableConceptInput, FhirInputModel


class PatientCommunicationInput(FhirInputModel):
    """Patient.communication — a language which may be used to communicate with
    the patient about his or her health (BackboneElement)."""

    language: FhirCodeableConceptInput = Field(
        ..., description="The language which can be used to communicate with the patient (required by R4)."
    )
    preferred: bool | None = Field(
        None, description="Language preference indicator."
    )

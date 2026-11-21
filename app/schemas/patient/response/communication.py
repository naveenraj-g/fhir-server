from pydantic import BaseModel, Field

from app.schemas.datatypes import FHIRCodeableConcept


class FHIRPatientCommunication(BaseModel):
    """Patient.communication — a language which may be used to communicate with
    the patient."""

    language: FHIRCodeableConcept = Field(
        ...,
        description="The language which can be used to communicate with the patient.",
    )
    preferred: bool | None = Field(None, description="Language preference indicator.")

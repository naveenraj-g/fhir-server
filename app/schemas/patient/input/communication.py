from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class PatientCommunicationInput(BaseModel):
    """Patient.communication — a language which may be used to communicate with the patient (BackboneElement)."""

    model_config = ConfigDict(extra="forbid")
    language_coding: list[CodingInput] | None = Field(
        None, description="Coding(s) for the language (e.g. urn:ietf:bcp:47 code 'en')."
    )
    language_text: str | None = Field(
        None, description="Plain text representation of the language."
    )
    preferred: bool | None = Field(
        None, description="Language preference indicator."
    )

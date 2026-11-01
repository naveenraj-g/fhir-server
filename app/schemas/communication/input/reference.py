from pydantic import BaseModel, ConfigDict, Field


class CommunicationReferenceInput(BaseModel):
    """Reference input for Communication (reference + optional display narrative)."""

    model_config = ConfigDict(extra="forbid")

    reference: str | None = Field(
        None, description="FHIR reference string (e.g. 'Patient/10001')."
    )
    display: str | None = Field(
        None, description="Plain text display narrative for reference."
    )

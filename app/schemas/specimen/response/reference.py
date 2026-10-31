from pydantic import BaseModel, ConfigDict, Field


class PlainSpecimenReference(BaseModel):
    """Plain response shape for references on Specimen."""

    model_config = ConfigDict(extra="allow")
    reference: str | None = Field(None, description="FHIR reference string, e.g. 'Patient/10001'.")
    id: int | None = Field(None, description="Target resource public sequence ID.")
    type: str | None = Field(None, description="Target resource type.")
    display: str | None = Field(None, description="Plain text display.")

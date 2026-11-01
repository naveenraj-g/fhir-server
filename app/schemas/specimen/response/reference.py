from pydantic import BaseModel, ConfigDict, Field


class PlainSpecimenReference(BaseModel):
    """Plain response shape for references on Specimen."""

    model_config = ConfigDict(extra="allow")
    reference: str | None = Field(None, description="FHIR reference string, e.g. 'Patient/10001'.")
    id: int | None = Field(None, description="Target resource public sequence ID.")
    type: str | None = Field(None, description="Target resource type.")
    display: str | None = Field(None, description="Plain text display.")
    identifier_use: str | None = None
    identifier_type_system: str | None = None
    identifier_type_version: str | None = None
    identifier_type_code: str | None = None
    identifier_type_display: str | None = None
    identifier_type_user_selected: bool | None = None
    identifier_type_text: str | None = None
    identifier_system: str | None = None
    identifier_value: str | None = None
    identifier_period_start: str | None = None
    identifier_period_end: str | None = None

from pydantic import ConfigDict, Field

from app.schemas.datatypes import AuditFields


class PlainCommunicationRequestReference(AuditFields):
    """Plain snake_case serialization of a CommunicationRequest reference child row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="DB primary key of this reference row.")
    reference_reference: str | None = Field(None, description="Raw literal reference string.")
    reference: str | None = Field(None, description="Computed reference string (e.g. 'Patient/10001').")
    reference_type: str | None = Field(None, description="Target resource type.")
    reference_id: int | None = Field(None, description="Target public ID.")
    reference_display: str | None = Field(None, description="Narrative display.")

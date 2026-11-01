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
    reference_identifier_use: str | None = Field(None, description="Fallback identifier purpose/use.")
    reference_identifier_type_system: str | None = Field(None, description="Fallback identifier type system.")
    reference_identifier_type_version: str | None = Field(None, description="Fallback identifier type version.")
    reference_identifier_type_code: str | None = Field(None, description="Fallback identifier type code.")
    reference_identifier_type_display: str | None = Field(None, description="Fallback identifier type display.")
    reference_identifier_type_text: str | None = Field(None, description="Fallback identifier type text.")
    reference_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier type user selected.")
    reference_identifier_system: str | None = Field(None, description="Fallback identifier namespace system.")
    reference_identifier_value: str | None = Field(None, description="Fallback identifier value.")
    reference_identifier_period_start: str | None = Field(None, description="Fallback identifier period start.")
    reference_identifier_period_end: str | None = Field(None, description="Fallback identifier period end.")

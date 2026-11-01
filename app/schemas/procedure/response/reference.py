from pydantic import ConfigDict, Field

from app.schemas.datatypes import AuditFields


class PlainProcedureReference(AuditFields):
    """Plain snake_case serialization of a Procedure reference child row."""

    model_config = ConfigDict(extra="allow")

    id: int | None = Field(None, description="DB primary key of this reference row.")
    reference: str | None = Field(None, description="Computed reference string (e.g. 'Condition/120001').")
    reference_reference: str | None = Field(None, description="Raw literal reference string.")
    reference_type: str | None = Field(None, description="Target resource type.")
    reference_id: int | None = Field(None, description="Target public ID.")
    reference_display: str | None = Field(None, description="Narrative display.")
    display: str | None = Field(None, description="Narrative display.")
    identifier_use: str | None = None
    identifier_type_system: str | None = None
    identifier_type_version: str | None = None
    identifier_type_code: str | None = None
    identifier_type_display: str | None = None
    identifier_type_text: str | None = None
    identifier_type_user_selected: bool | None = None
    identifier_system: str | None = None
    identifier_value: str | None = None
    identifier_period_start: str | None = None
    identifier_period_end: str | None = None
    reference_identifier_use: str | None = None
    reference_identifier_type_system: str | None = None
    reference_identifier_type_version: str | None = None
    reference_identifier_type_code: str | None = None
    reference_identifier_type_display: str | None = None
    reference_identifier_type_text: str | None = None
    reference_identifier_type_user_selected: bool | None = None
    reference_identifier_system: str | None = None
    reference_identifier_value: str | None = None
    reference_identifier_period_start: str | None = None
    reference_identifier_period_end: str | None = None

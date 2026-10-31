from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import AuditFields, PlainCodingRow
from app.schemas.enums import IdentifierUse


class PlainFlagIdentifier(AuditFields):
    """Plain snake_case serialization of a Flag identifier child row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="DB primary key of this identifier row.")
    use: IdentifierUse | None = Field(None, description="usual|official|temp|secondary|old.")
    type_text: str | None = Field(None, description="Plain text type display.")
    type_codings: list[PlainCodingRow] | None = Field(
        None, description="Grandchild coding rows for identifier.type."
    )
    system: str | None = Field(None, description="Namespace URL.")
    value: str | None = Field(None, description="Identifier value string.")
    period_start: str | None = Field(None, description="Start of validity period.")
    period_end: str | None = Field(None, description="End of validity period.")
    assigner_reference: str | None = Field(None, description="Literal assigner reference string.")
    assigner: str | None = Field(None, description="Computed assigner reference (e.g. 'Organization/190001').")
    assigner_type: str | None = Field(None, description="Target type of assigner reference.")
    assigner_id: int | None = Field(None, description="Resolved public ID of assigner.")
    assigner_display: str | None = Field(None, description="Display text for assigner.")
    assigner_identifier_use: IdentifierUse | None = Field(None)
    assigner_identifier_type_system: str | None = Field(None)
    assigner_identifier_type_version: str | None = Field(None)
    assigner_identifier_type_code: str | None = Field(None)
    assigner_identifier_type_display: str | None = Field(None)
    assigner_identifier_type_text: str | None = Field(None)
    assigner_identifier_type_user_selected: bool | None = Field(None)
    assigner_identifier_system: str | None = Field(None)
    assigner_identifier_value: str | None = Field(None)
    assigner_identifier_period_start: str | None = Field(None)
    assigner_identifier_period_end: str | None = Field(None)

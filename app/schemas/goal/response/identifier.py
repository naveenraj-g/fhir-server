from pydantic import ConfigDict, Field

from app.schemas.datatypes import AuditFields, PlainCodingRow
from app.schemas.enums import IdentifierUse


class PlainGoalIdentifier(AuditFields):
    """Plain snake_case serialization of a Goal identifier child row."""

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

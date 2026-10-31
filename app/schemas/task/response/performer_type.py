from pydantic import ConfigDict, Field

from app.schemas.datatypes import AuditFields, PlainCodingRow


class PlainTaskPerformerType(AuditFields):
    """Plain snake_case serialization of a Task performer_type child row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="DB primary key of this performer_type row.")
    text: str | None = Field(None, description="Plain text concept representation.")
    codings: list[PlainCodingRow] | None = Field(
        None, description="Grandchild coding rows."
    )

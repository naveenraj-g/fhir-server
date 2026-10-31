from pydantic import ConfigDict, Field

from app.schemas.datatypes import AuditFields, PlainCodingRow


class PlainFlagCategory(AuditFields):
    """Plain snake_case serialization of a Flag.category child row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="DB primary key of this category row.")
    text: str | None = Field(None, description="Plain text representation of category.")
    codings: list[PlainCodingRow] | None = Field(
        None, description="Grandchild coding rows for category."
    )

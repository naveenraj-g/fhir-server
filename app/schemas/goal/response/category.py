from pydantic import ConfigDict, Field

from app.schemas.datatypes import AuditFields, PlainCodingRow


class PlainGoalCategory(AuditFields):
    """Plain snake_case serialization of a Goal category / outcomeCode / codeable concept."""

    model_config = ConfigDict(extra="allow")

    id: int | None = Field(None, description="DB primary key of this row (if child table).")
    text: str | None = Field(None, description="Plain text representation.")
    codings: list[PlainCodingRow] | None = Field(
        None, description="Coding rows for this concept."
    )

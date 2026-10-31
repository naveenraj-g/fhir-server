from pydantic import ConfigDict, Field

from app.schemas.datatypes import AuditFields, PlainCodingRow


class PlainCommunicationRequestCategory(AuditFields):
    """Plain snake_case serialization of CommunicationRequest category / medium / reasonCode child row."""

    model_config = ConfigDict(extra="allow")

    id: int | None = Field(None, description="DB primary key of this row.")
    text: str | None = Field(None, description="Plain text representation.")
    codings: list[PlainCodingRow] | None = Field(
        None, description="Coding rows for this concept."
    )

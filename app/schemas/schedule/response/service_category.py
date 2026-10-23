from pydantic import Field

from app.schemas.datatypes import AuditFields, PlainCodingRow


class PlainScheduleServiceCategory(AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    codings: list[PlainCodingRow] | None = Field(
        None, description="Coding(s) for this service category."
    )
    text: str | None = Field(
        None, description="A human language representation of the category."
    )

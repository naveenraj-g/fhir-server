from pydantic import Field

from app.schemas.datatypes import AuditFields


class PlainLocationAlias(AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    value: str | None = Field(
        None,
        description="An alternate name the location is known as, or was known as in the past.",
    )

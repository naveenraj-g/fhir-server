from pydantic import Field

from app.schemas.datatypes import AuditFields


class PlainOrganizationAlias(AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    value: str | None = Field(
        None,
        description="An alternate name the organization is known as, or was known as in the past.",
    )

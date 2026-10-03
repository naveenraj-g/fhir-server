from pydantic import Field

from ._shared import PlainOrganizationCoding, _AuditFields


class PlainOrganizationType(_AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    codings: list[PlainOrganizationCoding] | None = Field(
        None, description="Coding(s) for this organization type."
    )
    text: str | None = Field(
        None, description="A human language representation of the organization type."
    )

from pydantic import Field

from app.schemas.datatypes import AuditFields, PlainCodingRow


class PlainRelatedPersonRelationship(AuditFields):
    id: int = Field(..., description="Internal row ID.")
    text: str | None = Field(
        None, description="Plain text representation of the relationship."
    )
    codings: list[PlainCodingRow] | None = Field(
        None, description="Coding(s) for the relationship."
    )

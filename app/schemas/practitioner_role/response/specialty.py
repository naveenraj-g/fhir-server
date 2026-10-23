from pydantic import Field

from app.schemas.datatypes import AuditFields, PlainCodingRow


class PlainPractitionerRoleSpecialty(AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    codings: list[PlainCodingRow] | None = Field(
        None, description="Coding(s) for this specialty."
    )
    text: str | None = Field(
        None, description="A human language representation of the specialty."
    )

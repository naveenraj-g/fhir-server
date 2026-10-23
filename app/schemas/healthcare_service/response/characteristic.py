from pydantic import Field

from app.schemas.datatypes import AuditFields, PlainCodingRow


class PlainHealthcareServiceCharacteristic(AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    codings: list[PlainCodingRow] | None = Field(
        None, description="Coding(s) for this characteristic."
    )
    text: str | None = Field(
        None, description="A human language representation of the characteristic."
    )

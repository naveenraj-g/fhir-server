from pydantic import Field

from ._shared import PlainHealthcareServiceCoding, _AuditFields


class PlainHealthcareServiceSpecialty(_AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    codings: list[PlainHealthcareServiceCoding] | None = Field(
        None, description="Coding(s) for this specialty."
    )
    text: str | None = Field(
        None, description="A human language representation of the specialty."
    )

from pydantic import Field

from ._shared import PlainHealthcareServiceCoding, _AuditFields


class PlainHealthcareServiceServiceProvisionCode(_AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    codings: list[PlainHealthcareServiceCoding] | None = Field(
        None, description="Coding(s) for this service provision code."
    )
    text: str | None = Field(
        None,
        description="A human language representation of the service provision code.",
    )

from pydantic import Field

from ._shared import PlainHealthcareServiceCoding, _AuditFields


class PlainHealthcareServiceReferralMethod(_AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    codings: list[PlainHealthcareServiceCoding] | None = Field(
        None, description="Coding(s) for this referral method."
    )
    text: str | None = Field(
        None, description="A human language representation of the referral method."
    )

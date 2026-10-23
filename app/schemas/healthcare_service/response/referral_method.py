from pydantic import Field

from app.schemas.datatypes import AuditFields, PlainCodingRow


class PlainHealthcareServiceReferralMethod(AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    codings: list[PlainCodingRow] | None = Field(
        None, description="Coding(s) for this referral method."
    )
    text: str | None = Field(
        None, description="A human language representation of the referral method."
    )

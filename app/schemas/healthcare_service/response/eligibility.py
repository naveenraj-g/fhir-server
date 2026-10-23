from pydantic import BaseModel, Field

from app.schemas.datatypes import AuditFields, FHIRCodeableConcept, PlainCodingRow


class FHIRHealthcareServiceEligibility(BaseModel):
    """HealthcareService.eligibility — FHIR camelCase BackboneElement."""

    code: FHIRCodeableConcept | None = Field(
        None, description="Coding(s) specific to the eligibility."
    )
    comment: str | None = Field(
        None,
        description="Describes the eligibility conditions in more detail (markdown).",
    )


class PlainHealthcareServiceEligibility(AuditFields):
    """`code_codings` is a real 0..* child table rather than a single
    flattened coding — code_text stays flattened (sibling of coding[],
    not part of it)."""

    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    code_codings: list[PlainCodingRow] | None = Field(
        None, description="Coding(s) for the eligibility code."
    )
    code_text: str | None = Field(
        None, description="A human language representation of the eligibility code."
    )
    comment: str | None = Field(
        None, description="Describes the eligibility conditions in more detail."
    )

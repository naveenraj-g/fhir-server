from pydantic import BaseModel, Field

from app.schemas.common.fhir import FHIRCodeableConcept

from ._shared import _AuditFields


class FHIRHealthcareServiceEligibility(BaseModel):
    """HealthcareService.eligibility — FHIR camelCase BackboneElement."""

    code: FHIRCodeableConcept | None = Field(
        None, description="Coding(s) specific to the eligibility."
    )
    comment: str | None = Field(
        None,
        description="Describes the eligibility conditions in more detail (markdown).",
    )


class PlainHealthcareServiceEligibility(_AuditFields):
    id: int = Field(..., description="Internal row ID — use for sub-resource lookups.")
    code_system: str | None = Field(
        None,
        description="The code system that defines the meaning of the eligibility code.",
    )
    code_version: str | None = Field(
        None, description="The version of the code system used."
    )
    code_code: str | None = Field(
        None, description="A symbol in syntax defined by the code system."
    )
    code_display: str | None = Field(
        None, description="A representation of the meaning of the eligibility code."
    )
    code_text: str | None = Field(
        None, description="A human language representation of the eligibility code."
    )
    code_user_selected: bool | None = Field(
        None, description="Whether this coding was chosen by a user directly."
    )
    comment: str | None = Field(
        None, description="Describes the eligibility conditions in more detail."
    )

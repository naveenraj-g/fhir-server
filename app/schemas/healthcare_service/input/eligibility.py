from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class HealthcareServiceEligibilityInput(BaseModel):
    """HealthcareService.eligibility — specific eligibility requirements for
    using the service (BackboneElement). `code_text` is the code
    CodeableConcept's own field (sibling of coding[], not part of it);
    `code_coding` is the real 0..* list — see CodingInput."""

    model_config = ConfigDict(extra="forbid")
    code_coding: list[CodingInput] | None = Field(
        None,
        description="Coding(s) for the eligibility code — may include both a custom code and a standard-terminology crosswalk.",
    )
    code_text: str | None = Field(
        None,
        description="A human language representation of the eligibility code, as seen/selected/entered by the user.",
    )
    comment: str | None = Field(
        None,
        description="Describes the eligibility conditions in more detail, as free text or an HTML fragment.",
    )

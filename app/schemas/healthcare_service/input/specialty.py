from pydantic import BaseModel, ConfigDict, Field

from ._shared import HealthcareServiceCodingInput


class HealthcareServiceSpecialtyInput(BaseModel):
    """HealthcareService.specialty — collection of specialties handled by
    the service site (CodeableConcept). `text` is the CodeableConcept's own
    field (sibling of coding[], not part of it); `coding` is the real 0..*
    list — see HealthcareServiceCodingInput."""

    model_config = ConfigDict(extra="forbid")
    coding: list[HealthcareServiceCodingInput] | None = Field(
        None,
        description="Coding(s) for this specialty — may include both a custom code and a standard-terminology crosswalk.",
    )
    text: str | None = Field(
        None,
        description="A human language representation of the specialty, as seen/selected/entered by the user.",
    )

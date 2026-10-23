from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class HealthcareServiceProgramInput(BaseModel):
    """HealthcareService.program — programs that this service is applicable
    to (CodeableConcept). `text` is the CodeableConcept's own field (sibling
    of coding[], not part of it); `coding` is the real 0..* list — see
    CodingInput."""

    model_config = ConfigDict(extra="forbid")
    coding: list[CodingInput] | None = Field(
        None,
        description="Coding(s) for this program — may include both a custom code and a standard-terminology crosswalk.",
    )
    text: str | None = Field(
        None,
        description="A human language representation of the program, as seen/selected/entered by the user.",
    )

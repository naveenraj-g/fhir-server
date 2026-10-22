from pydantic import BaseModel, ConfigDict, Field

from ._shared import HealthcareServiceCodingInput


class HealthcareServiceCommunicationInput(BaseModel):
    """HealthcareService.communication — languages that people who work
    at/perform the service can use (CodeableConcept). `text` is the
    CodeableConcept's own field (sibling of coding[], not part of it);
    `coding` is the real 0..* list — see HealthcareServiceCodingInput."""

    model_config = ConfigDict(extra="forbid")
    coding: list[HealthcareServiceCodingInput] | None = Field(
        None,
        description="Coding(s) for this communication language — may include both a custom code and a standard-terminology crosswalk.",
    )
    text: str | None = Field(
        None,
        description="A human language representation of the communication language, as seen/selected/entered by the user.",
    )

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class PractitionerCommunicationInput(BaseModel):
    """Practitioner.communication — languages the practitioner can use in
    patient communication (CodeableConcept). `text` is the CodeableConcept's
    own field (sibling of coding[], not part of it); `coding` is the real
    0..* list — see app.schemas.datatypes.CodingInput."""

    model_config = ConfigDict(extra="forbid")
    coding: list[CodingInput] | None = Field(
        None,
        description="Coding(s) for this language — may include both a custom code and a standard-terminology (e.g. BCP-47/IETF) crosswalk.",
    )
    text: str | None = Field(
        None,
        description="A human language representation of the language, as seen/selected/entered by the user.",
    )

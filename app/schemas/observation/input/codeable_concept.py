from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class ObservationCodeableConceptInput(BaseModel):
    """Shared shape for every plain CodeableConcept field/list-item on
    Observation (category[], code, dataAbsentReason, interpretation[],
    bodySite, method, referenceRange.type, referenceRange.appliesTo[],
    component.code, component.dataAbsentReason, component.interpretation[],
    component.referenceRange.type, component.referenceRange.appliesTo[])
    — all the same {coding[], text} shape."""

    model_config = ConfigDict(extra="forbid")
    coding: list[CodingInput] | None = Field(None, description="Coding(s) for this concept.")
    text: str | None = Field(None, description="A human language representation of the concept.")

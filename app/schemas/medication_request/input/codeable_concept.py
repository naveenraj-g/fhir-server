from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class MedicationRequestCodeableConceptInput(BaseModel):
    """Shared shape for every plain CodeableConcept field/list-item on
    MedicationRequest (category[], reasonCode[], statusReason,
    medicationCodeableConcept, performerType, courseOfTherapyType,
    substitution.allowedCodeableConcept, substitution.reason, and the
    dosageInstruction-nested site/route/method/asNeededCodeableConcept/
    additionalInstruction[]) — all the same {coding[], text} shape."""

    model_config = ConfigDict(extra="forbid")
    coding: list[CodingInput] | None = Field(None, description="Coding(s) for this concept.")
    text: str | None = Field(None, description="A human language representation of the concept.")

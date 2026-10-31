from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class ConditionCodeableConceptInput(BaseModel):
    """Shared shape for CodeableConcept fields on Condition
    (clinicalStatus, verificationStatus, category[], severity, code, bodySite[],
    stage.summary, stage.type, evidence.code[])."""

    model_config = ConfigDict(extra="forbid")
    coding: list[CodingInput] | None = Field(
        None, description="Coding(s) for this concept."
    )
    text: str | None = Field(
        None, description="A human language representation of the concept."
    )

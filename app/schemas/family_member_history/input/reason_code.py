from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class FamilyMemberHistoryReasonCodeInput(BaseModel):
    """FamilyMemberHistory.reasonCode (0..* CodeableConcept)."""

    model_config = ConfigDict(extra="forbid")

    coding: list[CodingInput] | None = Field(
        None, description="Coding(s) for this reason."
    )
    text: str | None = Field(
        None, description="Plain text representation of the reason code."
    )

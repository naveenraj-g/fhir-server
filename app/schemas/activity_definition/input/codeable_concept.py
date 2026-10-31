from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class ActivityDefinitionCodeableConceptInput(BaseModel):
    """CodeableConcept input for ActivityDefinition."""

    model_config = ConfigDict(extra="forbid")

    coding: list[CodingInput] | None = Field(
        None, description="Code defined by a terminology system."
    )
    text: str | None = Field(
        None, description="Plain text representation of the concept."
    )

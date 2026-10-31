from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class SpecimenCodeableConceptInput(BaseModel):
    """Shared shape for CodeableConcept fields on Specimen."""

    model_config = ConfigDict(extra="forbid")
    coding: list[CodingInput] | None = Field(
        None, description="Coding(s) for this concept."
    )
    text: str | None = Field(
        None, description="A human language representation of the concept."
    )

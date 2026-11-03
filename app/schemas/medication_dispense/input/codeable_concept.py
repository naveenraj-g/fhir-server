from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class MedicationDispenseCodeableConceptInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str | None = Field(None, description="Plain text representation of the concept.")
    coding: list[CodingInput] | None = Field(None, description="Code defined by a terminology system.")

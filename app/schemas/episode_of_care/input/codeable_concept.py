from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class EpisodeOfCareCodeableConceptInput(BaseModel):
    """Input representation of a CodeableConcept for EpisodeOfCare."""

    model_config = ConfigDict(extra="forbid")

    text: str | None = Field(None, description="Plain text representation of the concept.")
    coding: list[CodingInput] | None = Field(
        None, description="Code defined by a terminology system."
    )

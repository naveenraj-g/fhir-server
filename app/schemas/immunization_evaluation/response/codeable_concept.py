from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow


class PlainImmunizationEvaluationCodeableConcept(BaseModel):
    """Plain snake_case CodeableConcept response."""

    model_config = ConfigDict(extra="forbid")

    coding: list[PlainCodingRow] | None = Field(
        None, description="Code defined by a terminology system."
    )
    text: str | None = Field(
        None, description="Plain text representation of the concept."
    )

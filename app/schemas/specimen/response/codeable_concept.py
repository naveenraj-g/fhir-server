from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow


class PlainSpecimenCodeableConcept(BaseModel):
    """Plain response shape for a CodeableConcept."""

    model_config = ConfigDict(extra="allow")
    text: str | None = Field(None, description="A human language representation of the concept.")
    codings: list[PlainCodingRow] | None = Field(None, description="Coding(s) for this concept.")


class PlainSpecimenCondition(BaseModel):
    """Plain response shape for Specimen.condition (0..*)."""

    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal DB ID.")
    text: str | None = Field(None, description="A human language representation of the condition.")
    codings: list[PlainCodingRow] | None = Field(None, description="Coding(s) for this condition.")

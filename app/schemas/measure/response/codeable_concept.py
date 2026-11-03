from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow


class PlainMeasureConcept(BaseModel):
    """Plain representation of a 0..* CodeableConcept child entry."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    text: str | None = None
    codings: list[PlainCodingRow] | None = None


class PlainMeasureSingleConcept(BaseModel):
    """Plain representation of a 0..1 CodeableConcept."""

    model_config = ConfigDict(extra="allow")

    text: str | None = None
    codings: list[PlainCodingRow] | None = None

from pydantic import BaseModel, ConfigDict

from app.schemas.datatypes import PlainCoding, PlainCodingRow


class PlainProcedureConcept(BaseModel):
    """Plain concept representation for 0..* child rows."""

    model_config = ConfigDict(extra="allow")

    id: int
    text: str | None = None
    codings: list[PlainCodingRow] | None = None


class PlainProcedureSingleConcept(BaseModel):
    """Plain concept representation for 0..1 fields."""

    model_config = ConfigDict(extra="allow")

    text: str | None = None
    codings: list[PlainCoding] | None = None

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCoding


class PlainGroupCodeableConcept(BaseModel):
    """Shared plain/snake_case representation for Group CodeableConcept fields."""

    model_config = ConfigDict(extra="ignore")

    coding: list[PlainCoding] | None = Field(
        None, description="Coding(s) for this concept."
    )
    text: str | None = Field(
        None, description="A human language representation of the concept."
    )

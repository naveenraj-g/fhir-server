from pydantic import BaseModel, ConfigDict

from app.schemas.datatypes import PlainCodingRow


class PlainAllergyIntoleranceCodeableConcept(BaseModel):
    """Plain representation of a CodeableConcept on AllergyIntolerance."""

    model_config = ConfigDict(extra="allow")

    text: str | None = None
    coding: list[PlainCodingRow] | None = None

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class RelatedPersonRelationshipInput(BaseModel):
    """RelatedPerson.relationship (0..* CodeableConcept)."""

    model_config = ConfigDict(extra="forbid")
    coding: list[CodingInput] | None = Field(
        None, description="Coding(s) identifying the relationship type."
    )
    text: str | None = Field(
        None, description="Plain text representation of the relationship."
    )

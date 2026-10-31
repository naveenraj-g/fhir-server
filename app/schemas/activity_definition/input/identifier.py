from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IdentifierUse
from app.schemas.datatypes import CodingInput


class ActivityDefinitionIdentifierInput(BaseModel):
    """ActivityDefinition.identifier input schema."""

    model_config = ConfigDict(extra="forbid")

    use: IdentifierUse | None = Field(None, description="usual | official | temp | secondary | old.")
    system: str | None = Field(None, description="The namespace for the identifier value.")
    value: str | None = Field(None, description="The value that is unique.")
    type_text: str | None = Field(None, description="Description of identifier type.")
    type_coding: list[CodingInput] | None = Field(None, description="Coding for identifier type.")
    period_start: datetime | None = Field(None, description="Time period when id is/was valid for use.")
    period_end: datetime | None = Field(None, description="Time period when id is/was valid for use.")
    assigner: str | None = Field(None, description="Organization that issued id (Organization/123).")
    assigner_display: str | None = Field(None, description="Organization display text.")

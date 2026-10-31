from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IdentifierUse
from app.schemas.datatypes import CodingInput


class CommunicationRequestIdentifierInput(BaseModel):
    """External Ids for this communication request."""

    model_config = ConfigDict(extra="forbid")

    use: IdentifierUse | None = Field(
        None, description="usual | official | temp | secondary | old."
    )
    type_coding: list[CodingInput] | None = Field(
        None, description="Description of identifier."
    )
    type_text: str | None = Field(
        None, description="Plain text representation of the type."
    )
    system: str | None = Field(
        None, description="The namespace for the identifier value."
    )
    value: str | None = Field(
        None, description="The value that is unique."
    )
    period_start: datetime | None = Field(
        None, description="Time period during which identifier is valid — start."
    )
    period_end: datetime | None = Field(
        None, description="Time period during which identifier is valid — end."
    )
    assigner: str | None = Field(
        None, description="Organization that issued id (Reference(Organization))."
    )
    assigner_display: str | None = Field(
        None, description="Plain text narrative for assigner reference."
    )

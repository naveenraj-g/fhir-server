from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IdentifierUse
from app.schemas.datatypes import CodingInput


class EpisodeOfCareIdentifierInput(BaseModel):
    """Input representation of an Identifier for EpisodeOfCare."""

    model_config = ConfigDict(extra="forbid")

    use: IdentifierUse | None = Field(None, description="usual | official | temp | secondary | old")
    type_text: str | None = Field(None, description="Description of identifier type.")
    type_codings: list[CodingInput] | None = Field(
        None, description="Codings for identifier type."
    )
    system: str | None = Field(None, description="The namespace for the identifier value.")
    value: str | None = Field(None, description="The value that is unique.")
    period_start: datetime | None = Field(None, description="Time period when id is/was valid.")
    period_end: datetime | None = Field(None, description="Time period when id is/was valid.")
    assigner: str | None = Field(
        None, description="Organization that issued id (Reference(Organization))."
    )
    assigner_display: str | None = Field(None, description="Display name for assigner.")
    assigner_identifier_use: IdentifierUse | None = Field(None, description="Assigner identifier use.")
    assigner_identifier_system: str | None = Field(None, description="Assigner identifier system.")
    assigner_identifier_value: str | None = Field(None, description="Assigner identifier value.")
    assigner_identifier_type_text: str | None = Field(
        None, description="Assigner identifier type text."
    )

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IdentifierUse
from app.schemas.group.input.codeable_concept import GroupCodeableConceptInput


class GroupIdentifierInput(BaseModel):
    """External identifier for Group."""

    model_config = ConfigDict(extra="forbid")

    use: IdentifierUse | None = Field(
        None, description="usual | official | temp | secondary | old"
    )
    type: GroupCodeableConceptInput | None = Field(
        None, description="Description of identifier."
    )
    system: str | None = Field(
        None, description="The namespace for the identifier value."
    )
    value: str | None = Field(None, description="The value that is unique.")
    period_start: datetime | None = Field(
        None, description="Time period during which identifier is/was valid (start)."
    )
    period_end: datetime | None = Field(
        None, description="Time period during which identifier is/was valid (end)."
    )
    assigner: str | None = Field(
        None, description="Organization that issued id (e.g. Organization/190001)."
    )
    assigner_display: str | None = Field(
        None, description="Plain text display for assigner."
    )

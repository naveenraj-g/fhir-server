from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class GroupMemberInput(BaseModel):
    """Who or what is in group."""

    model_config = ConfigDict(extra="forbid")

    entity: str = Field(
        ...,
        description="Reference to the group member (Patient | Practitioner | PractitionerRole | Device | Medication | Substance | Group).",
    )
    entity_display: str | None = Field(
        None, description="Plain text display for member entity."
    )
    period_start: datetime | None = Field(
        None, description="Period member belongs to the group (start)."
    )
    period_end: datetime | None = Field(
        None, description="Period member belongs to the group (end)."
    )
    inactive: bool | None = Field(
        None, description="If member is no longer in group."
    )

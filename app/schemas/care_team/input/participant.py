from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.care_team.input.codeable_concept import (
    CareTeamCodeableConceptInput,
)


class CareTeamParticipantInput(BaseModel):
    """CareTeam.participant entry."""

    model_config = ConfigDict(extra="forbid")

    role: list[CareTeamCodeableConceptInput] | None = Field(
        None, description="Type of role (e.g. 'primary care physician', 'consultant')."
    )
    member: str | None = Field(
        None,
        description="Who is involved (e.g. 'Practitioner/30001', 'Patient/10001', 'Organization/190001').",
    )
    member_display: str | None = Field(
        None, description="Display name for member reference."
    )
    on_behalf_of: str | None = Field(
        None,
        description="Organization of the individual (e.g. 'Organization/190001').",
    )
    on_behalf_of_display: str | None = Field(
        None, description="Display name for onBehalfOf reference."
    )
    period_start: datetime | None = Field(
        None, description="Time period of participant's involvement — start."
    )
    period_end: datetime | None = Field(
        None, description="Time period of participant's involvement — end."
    )

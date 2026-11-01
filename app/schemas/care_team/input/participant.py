from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.care_team.input.codeable_concept import (
    CareTeamCodeableConceptInput,
)
from app.schemas.enums import IdentifierUse


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
    member_identifier_use: IdentifierUse | None = Field(None)
    member_identifier_type_system: str | None = Field(None)
    member_identifier_type_version: str | None = Field(None)
    member_identifier_type_code: str | None = Field(None)
    member_identifier_type_display: str | None = Field(None)
    member_identifier_type_user_selected: bool | None = Field(None)
    member_identifier_type_text: str | None = Field(None)
    member_identifier_system: str | None = Field(None)
    member_identifier_value: str | None = Field(None)
    member_identifier_period_start: datetime | None = Field(None)
    member_identifier_period_end: datetime | None = Field(None)

    on_behalf_of: str | None = Field(
        None,
        description="Organization of the individual (e.g. 'Organization/190001').",
    )
    on_behalf_of_display: str | None = Field(
        None, description="Display name for onBehalfOf reference."
    )
    on_behalf_of_identifier_use: IdentifierUse | None = Field(None)
    on_behalf_of_identifier_type_system: str | None = Field(None)
    on_behalf_of_identifier_type_version: str | None = Field(None)
    on_behalf_of_identifier_type_code: str | None = Field(None)
    on_behalf_of_identifier_type_display: str | None = Field(None)
    on_behalf_of_identifier_type_user_selected: bool | None = Field(None)
    on_behalf_of_identifier_type_text: str | None = Field(None)
    on_behalf_of_identifier_system: str | None = Field(None)
    on_behalf_of_identifier_value: str | None = Field(None)
    on_behalf_of_identifier_period_start: datetime | None = Field(None)
    on_behalf_of_identifier_period_end: datetime | None = Field(None)

    period_start: datetime | None = Field(
        None, description="Time period of participant's involvement — start."
    )
    period_end: datetime | None = Field(
        None, description="Time period of participant's involvement — end."
    )

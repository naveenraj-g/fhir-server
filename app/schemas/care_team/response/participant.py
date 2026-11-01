from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRPeriod,
    FHIRReference,
    PlainCodingRow,
)


class FHIRCareTeamParticipant(BaseModel):
    """FHIR R4 CareTeam.participant backbone element."""

    model_config = ConfigDict(extra="forbid")

    role: list[FHIRCodeableConcept] | None = Field(
        None, description="Type of role."
    )
    member: FHIRReference | None = Field(
        None, description="Who is involved (Reference)."
    )
    onBehalfOf: FHIRReference | None = Field(
        None, description="Organization of the individual (Reference(Organization))."
    )
    period: FHIRPeriod | None = Field(
        None, description="Time period of participant's involvement."
    )


class PlainCareTeamParticipantRole(BaseModel):
    """Plain response shape for participant role."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    text: str | None = None
    codings: list[PlainCodingRow] | None = None


class PlainCareTeamParticipant(BaseModel):
    """Plain response shape for CareTeam.participant."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    roles: list[PlainCareTeamParticipantRole] | None = None
    member: str | None = None
    member_type: str | None = None
    member_id: int | None = None
    member_display: str | None = None
    member_identifier_use: str | None = None
    member_identifier_type_system: str | None = None
    member_identifier_type_version: str | None = None
    member_identifier_type_code: str | None = None
    member_identifier_type_display: str | None = None
    member_identifier_type_user_selected: bool | None = None
    member_identifier_type_text: str | None = None
    member_identifier_system: str | None = None
    member_identifier_value: str | None = None
    member_identifier_period_start: datetime | None = None
    member_identifier_period_end: datetime | None = None

    on_behalf_of: str | None = None
    on_behalf_of_type: str | None = None
    on_behalf_of_id: int | None = None
    on_behalf_of_display: str | None = None
    on_behalf_of_identifier_use: str | None = None
    on_behalf_of_identifier_type_system: str | None = None
    on_behalf_of_identifier_type_version: str | None = None
    on_behalf_of_identifier_type_code: str | None = None
    on_behalf_of_identifier_type_display: str | None = None
    on_behalf_of_identifier_type_user_selected: bool | None = None
    on_behalf_of_identifier_type_text: str | None = None
    on_behalf_of_identifier_system: str | None = None
    on_behalf_of_identifier_value: str | None = None
    on_behalf_of_identifier_period_start: datetime | None = None
    on_behalf_of_identifier_period_end: datetime | None = None

    period_start: datetime | None = None
    period_end: datetime | None = None

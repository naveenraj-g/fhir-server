from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.datatypes import PlainCodingRow


class PlainCareTeamIdentifier(BaseModel):
    """Plain response shape for CareTeam.identifier."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    use: str | None = None
    type_text: str | None = None
    system: str | None = None
    value: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    assigner: str | None = None
    assigner_type: str | None = None
    assigner_id: int | None = None
    assigner_display: str | None = None
    assigner_identifier_use: str | None = None
    assigner_identifier_system: str | None = None
    assigner_identifier_value: str | None = None
    assigner_identifier_type_text: str | None = None
    type_codings: list[PlainCodingRow] | None = None

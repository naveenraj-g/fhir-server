from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlainCareTeamNote(BaseModel):
    """Plain response shape for CareTeam.note."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    author_string: str | None = None
    author_reference: str | None = None
    author_reference_type: str | None = None
    author_reference_id: int | None = None
    author_reference_display: str | None = None
    time: datetime | None = None
    text: str | None = None

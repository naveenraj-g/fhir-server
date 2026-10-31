from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.datatypes import AuditFields, PlainCodingRow


class PlainEpisodeOfCareIdentifier(AuditFields, BaseModel):
    """Plain response representation of an EpisodeOfCare identifier."""

    model_config = ConfigDict(extra="forbid")

    id: int
    use: str | None = None
    type_text: str | None = None
    system: str | None = None
    value: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    assigner_reference: str | None = None
    assigner_type: str | None = None
    assigner_id: int | None = None
    assigner_display: str | None = None
    type_codings: list[PlainCodingRow] = []

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow


class PlainMeasureIdentifier(BaseModel):
    """Plain representation of a Measure identifier row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    use: str | None = None
    type_text: str | None = None
    type_codings: list[PlainCodingRow] | None = None
    system: str | None = None
    value: str | None = None
    period_start: dt.datetime | None = None
    period_end: dt.datetime | None = None
    assigner: str | None = None
    assigner_display: str | None = None

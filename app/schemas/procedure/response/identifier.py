from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainIdentifierType
from app.schemas.enums import IdentifierUse


class PlainProcedureIdentifier(BaseModel):
    """Plain representation of ProcedureIdentifier child row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    use: IdentifierUse | None = None
    type: PlainIdentifierType | None = None
    system: str | None = None
    value: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    assigner: str | None = None
    assigner_display: str | None = None

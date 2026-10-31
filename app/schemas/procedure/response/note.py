from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlainProcedureNote(BaseModel):
    """Plain representation of ProcedureNote."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    author_string: str | None = None
    author_reference: str | None = None
    author_reference_display: str | None = None
    time: datetime | None = None
    text: str | None = None

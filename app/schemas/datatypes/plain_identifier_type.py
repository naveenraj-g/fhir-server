from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.datatypes.plain_coding import PlainCoding


class PlainIdentifierType(BaseModel):
    """Plain-JSON rendering of Identifier.type — a coded description of the identifier's type."""

    text: Optional[str] = Field(None, description="Plain-text rendering of the identifier-type concept.")
    coding: Optional[List[PlainCoding]] = Field(None, description="Coded value(s) for the identifier type.")

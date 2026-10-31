from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PlainAllergyIntoleranceNote(BaseModel):
    """Plain representation of AllergyIntoleranceNote child row."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    text: str = Field(..., description="The annotation content as text.")
    time: datetime | None = None
    author_string: str | None = None
    author_reference: str | None = None
    author_reference_display: str | None = None

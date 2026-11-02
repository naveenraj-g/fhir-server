from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImmunizationEducationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_type: str | None = Field(None, description="Educational material document identifier.")
    reference: str | None = Field(None, description="Educational material reference pointer (URI).")
    publication_date: datetime | None = Field(None, description="Educational material publication date.")
    presentation_date: datetime | None = Field(None, description="Educational material presentation date.")

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FHIRImmunizationEducation(BaseModel):
    model_config = ConfigDict(extra="allow")

    documentType: str | None = Field(None, description="Educational material document identifier.")
    reference: str | None = Field(None, description="Educational material reference pointer (URI).")
    publicationDate: str | None = Field(None, description="Educational material publication date.")
    presentationDate: str | None = Field(None, description="Educational material presentation date.")


class PlainImmunizationEducation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID.")
    document_type: str | None = Field(None, description="Educational material document identifier.")
    reference: str | None = Field(None, description="Educational material reference pointer (URI).")
    publication_date: datetime | None = Field(None, description="Educational material publication date.")
    presentation_date: datetime | None = Field(None, description="Educational material presentation date.")

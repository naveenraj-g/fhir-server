from pydantic import BaseModel, ConfigDict, Field


class PlainServiceRequestNote(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal row ID.")
    author_string: str | None = Field(None, description="author[x]: string.")
    author_reference: str | None = Field(None, description="author[x]: Reference — resolved FHIR reference.")
    author_reference_type: str | None = Field(None, description="author[x]: Reference — resolved target type.")
    author_id: int | None = Field(None, description="author[x]: Reference — internal ID of the resolved target, if any.")
    author_display: str | None = Field(None, description="author[x]: Reference — plain text display.")
    time: str | None = Field(None, description="When this comment/annotation was made.")
    text: str | None = Field(None, description="The annotation text.")

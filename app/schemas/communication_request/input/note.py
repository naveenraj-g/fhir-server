from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CommunicationRequestNoteInput(BaseModel):
    """Annotation note for CommunicationRequest."""

    model_config = ConfigDict(extra="forbid")

    author_string: str | None = Field(
        None, description="Individual responsible for the annotation as a string."
    )
    author_reference: str | None = Field(
        None, description="Individual responsible for the annotation as a reference."
    )
    author_display: str | None = Field(
        None, description="Display name for author reference."
    )
    time: datetime | None = Field(
        None, description="When the annotation was made."
    )
    text: str = Field(
        ..., description="The annotation text content."
    )

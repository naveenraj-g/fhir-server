from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import AttachmentInput, CodingInput


class DocumentReferenceContentInput(BaseModel):
    """DocumentReference.content entry."""

    model_config = ConfigDict(extra="forbid")
    attachment: AttachmentInput = Field(
        ..., description="Document referenced — inline data or external URL."
    )
    format: CodingInput | None = Field(
        None, description="Format/content rules for the document."
    )

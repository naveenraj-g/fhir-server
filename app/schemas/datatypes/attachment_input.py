from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AttachmentInput(BaseModel):
    """One Attachment entry (e.g. `photo[]`) — reused wherever a resource
    embeds Attachment content, whether 0..1 (flattened directly on the
    owning table, e.g. HealthcareService.photo — see that resource's own
    hand-declared `photo_*` columns, which predate this shared type) or
    0..* (a dedicated child table, e.g. Practitioner.photo)."""

    model_config = ConfigDict(extra="forbid")
    content_type: Optional[str] = Field(
        None, description="Mime type of the content, with charset etc."
    )
    language: Optional[str] = Field(
        None, description="Human language of the content, as a BCP-47 code."
    )
    data: Optional[str] = Field(None, description="The actual data, base64-encoded.")
    url: Optional[str] = Field(
        None, description="A URI where the data can be found instead of inline."
    )
    size: Optional[int] = Field(
        None,
        description="Number of bytes of content, measured after decoding, if applicable.",
    )
    hash: Optional[str] = Field(
        None, description="Base64-encoded hash (SHA-1) of the data."
    )
    title: Optional[str] = Field(
        None, description="Label to display in place of the content."
    )
    creation: Optional[datetime] = Field(
        None, description="Datetime the attachment was first created."
    )

from typing import Optional
from pydantic import BaseModel, Field


class FHIRAttachment(BaseModel):
    """FHIR R4 Attachment — content in a format defined elsewhere."""

    contentType: Optional[str] = Field(
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
    creation: Optional[str] = Field(
        None, description="ISO 8601 datetime the attachment was first created."
    )

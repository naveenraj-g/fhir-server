from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PhotoCreate(BaseModel):
    """FHIR R4 Attachment — an image of the patient."""

    model_config = ConfigDict(extra="forbid")
    content_type: str | None = Field(
        None,
        description="MIME type of the content, with charset if applicable (e.g. image/png).",
    )
    language: str | None = Field(
        None,
        description="Human language of the content, as a BCP-47 code (e.g. en, fr).",
    )
    data: str | None = Field(None, description="The actual image data, base64-encoded.")
    url: str | None = Field(
        None,
        description="A URL where the image data can be retrieved instead of inline.",
    )
    size: int | None = Field(
        None,
        description="Number of bytes of content, measured after decoding from base64 if applicable.",
    )
    hash: str | None = Field(
        None,
        description="Base64-encoded hash (SHA-1) of the image data, used to verify integrity.",
    )
    title: str | None = Field(
        None, description="Label to display in place of the image content."
    )
    creation: datetime | None = Field(
        None, description="Date the image attachment was first created."
    )


class PhotoPatch(BaseModel):
    """Partial update to a photo attachment — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")
    content_type: str | None = Field(None, description="MIME type (e.g. image/png).")
    language: str | None = Field(None, description="BCP-47 language code.")
    data: str | None = Field(None, description="Base64-encoded image data.")
    url: str | None = Field(None, description="URL where the image can be retrieved.")
    size: int | None = Field(None, description="Size in bytes, after base64 decoding.")
    hash: str | None = Field(
        None, description="Base64-encoded SHA-1 hash of the image data."
    )
    title: str | None = Field(None, description="Label or display title.")
    creation: datetime | None = Field(None, description="When the image was created.")

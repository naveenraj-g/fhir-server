from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class PractitionerPhotoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content_type: str | None = Field(None, description="MIME type (e.g. image/png).")
    language: str | None = Field(None, description="BCP-47 language code.")
    data: str | None = Field(None, description="Base64-encoded image data.")
    url: str = Field(..., description="URL where the image can be retrieved.")
    size: int | None = Field(None, description="Size in bytes before base64 encoding.")
    hash: str | None = Field(None, description="Base64-encoded SHA-1 hash of the data.")
    title: str | None = Field(None, description="Label or display title.")
    creation: datetime | None = Field(None, description="When the image was created.")


class PractitionerPhotoPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content_type: str | None = None
    language: str | None = None
    data: str | None = None
    url: str | None = None
    size: int | None = None
    hash: str | None = None
    title: str | None = None
    creation: datetime | None = None

from pydantic import BaseModel, Field


class FHIRAttachment(BaseModel):
    contentType: str | None = Field(None, description="MIME type (e.g. image/png).")
    language: str | None = Field(None, description="BCP-47 language code.")
    data: str | None = Field(None, description="Base64-encoded binary data.")
    url: str | None = Field(None, description="URL where data can be accessed.")
    size: int | None = Field(None, description="Bytes before base64 encoding.")
    hash: str | None = Field(None, description="Base64-encoded SHA-1 hash.")
    title: str | None = Field(None, description="Label or display title.")
    creation: str | None = Field(None, description="ISO 8601 dateTime when created.")


class PlainPractitionerPhoto(BaseModel):
    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
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
    creation: str | None = Field(None, description="ISO 8601 datetime string.")
    created_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was created."
    )
    updated_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was last updated."
    )
    created_by: str | None = Field(
        None, description="Acting-user value recorded as the creator of this row."
    )
    updated_by: str | None = Field(
        None, description="Acting-user value recorded as the last updater of this row."
    )


class PractitionerPhotosListResponse(BaseModel):
    data: list[PlainPractitionerPhoto]
    total: int = Field(..., description="Total count of photo entries.")


class FHIRPractitionerPhotoListItem(FHIRAttachment):
    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPractitionerPhotosListResponse(BaseModel):
    data: list[FHIRPractitionerPhotoListItem]
    total: int = Field(..., description="Total count of photo entries.")

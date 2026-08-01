from pydantic import BaseModel, Field


class FHIRAttachment(BaseModel):
    """FHIR R4 Attachment — an image of the patient."""

    contentType: str | None = Field(
        None,
        description="Mime type of the content, with charset etc. (e.g. image/png).",
    )
    language: str | None = Field(
        None,
        description="Human language of the content, as a BCP-47 code (e.g. en, fr).",
    )
    data: str | None = Field(None, description="The actual image data, base64-encoded.")
    url: str | None = Field(
        None, description="A URI where the image data can be found instead of inline."
    )
    size: int | None = Field(
        None,
        description="Number of bytes of content, measured after decoding, if applicable.",
    )
    hash: str | None = Field(
        None,
        description="Base64-encoded hash (SHA-1) of the image data, used to verify integrity.",
    )
    title: str | None = Field(
        None, description="Label to display in place of the image content."
    )
    creation: str | None = Field(
        None, description="ISO 8601 datetime the image attachment was first created."
    )


class PlainPatientPhoto(BaseModel):
    """Plain-JSON Attachment — an image of the patient."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    content_type: str | None = Field(None, description="MIME type (e.g. image/png).")
    language: str | None = Field(None, description="BCP-47 language code.")
    data: str | None = Field(None, description="Base64-encoded image data.")
    url: str | None = Field(None, description="URL where the image can be retrieved.")
    size: int | None = Field(None, description="Size in bytes, after base64 decoding.")
    hash: str | None = Field(
        None, description="Base64-encoded SHA-1 hash of the image data."
    )
    title: str | None = Field(None, description="Label or display title.")
    creation: str | None = Field(
        None, description="ISO 8601 datetime the image was created."
    )
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


class PatientPhotosListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/photos."""

    data: list[PlainPatientPhoto] = Field(
        ..., description="Photo attachment entries for the patient."
    )
    total: int = Field(..., description="Total count of photo entries.")


class FHIRPatientPhotoListItem(FHIRAttachment):
    """FHIRAttachment plus the internal row id, for the GET /{patient_id}/photos list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientPhotosListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/photos."""

    data: list[FHIRPatientPhotoListItem] = Field(
        ..., description="Photo attachment entries for the patient."
    )
    total: int = Field(..., description="Total count of photo entries.")

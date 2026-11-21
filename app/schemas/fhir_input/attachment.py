from pydantic import Field

from app.schemas.fhir_input.base import FhirInputModel


class FhirAttachmentInput(FhirInputModel):
    """FHIR R4 Attachment — content in a format defined elsewhere."""

    contentType: str | None = Field(
        None, description="Mime type of the content, with charset etc."
    )
    language: str | None = Field(
        None, description="Human language of the content, as a BCP-47 code."
    )
    data: str | None = Field(None, description="The actual data, base64-encoded.")
    url: str | None = Field(
        None, description="A URI where the data can be found instead of inline."
    )
    size: int | None = Field(
        None, description="Number of bytes of content (if the value is inline)."
    )
    hash: str | None = Field(None, description="Base64-encoded SHA-1 hash of the data.")
    title: str | None = Field(
        None, description="Label to display in place of the content."
    )
    creation: str | None = Field(
        None, description="Date attachment was first created (ISO 8601)."
    )

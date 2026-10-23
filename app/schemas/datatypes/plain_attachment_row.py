from typing import Optional
from pydantic import Field

from app.schemas.datatypes.audit_fields import AuditFields


class PlainAttachmentRow(AuditFields):
    """One stored Attachment row — plain/snake_case rendering plus the
    row's own DB identity and audit trail. Shared by every resource's
    `photo[]`-style child table (Practitioner.photo, ...)."""

    id: int = Field(..., description="Internal row ID.")
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
    creation: Optional[str] = Field(
        None, description="ISO 8601 datetime the attachment was first created."
    )

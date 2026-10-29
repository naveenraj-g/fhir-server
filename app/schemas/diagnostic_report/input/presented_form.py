from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DiagnosticReportPresentedFormInput(BaseModel):
    """One entry of DiagnosticReport.presentedForm (0..* Attachment) —
    the full report as issued, e.g. a PDF."""

    model_config = ConfigDict(extra="forbid")
    content_type: str | None = Field(None, description="Mime type of the content, with charset etc.")
    language: str | None = Field(None, description="Human language of the content (BCP-47).")
    data: str | None = Field(None, description="Base64-encoded content, when the data is contained inline.")
    url: str | None = Field(None, description="URI where the data can be found.")
    size: int | None = Field(None, description="Number of bytes of content, after decoding (not encoded size).")
    hash: str | None = Field(None, description="Base64-encoded SHA-1 hash of the data.")
    title: str | None = Field(None, description="Label to display in place of the data.")
    creation: datetime | None = Field(None, description="Date the attachment was first created.")

from pydantic import BaseModel, ConfigDict, Field


class PlainDiagnosticReportMedia(BaseModel):
    """DiagnosticReport.media (0..* — a real child-table row)."""

    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal row ID.")
    comment: str | None = Field(None, description="Explanation of why the image is included or what it highlights.")
    link: str | None = Field(None, description="Resolved FHIR reference to the Media resource.")
    link_id: int | None = Field(None, description="Internal ID of the resolved Media, if any.")
    link_display: str | None = Field(None, description="Plain text narrative identifying the target.")

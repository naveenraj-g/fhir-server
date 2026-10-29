from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class DiagnosticReportMediaInput(BaseModel):
    """DiagnosticReport.media (0..* BackboneElement). `link` (1..1
    Reference(Media)) is flattened with the `link_*` prefix, same
    fallback-identifier shape as every other Reference field."""

    model_config = ConfigDict(extra="forbid")

    comment: str | None = Field(None, description="Explanation of why the image is included or what it highlights.")

    link_reference: str | None = Field(None, description="FHIR reference string, e.g. 'Media/1'.")
    link_display: str | None = Field(None, description="Plain text narrative identifying the target.")
    link_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — its purpose, if known.")
    link_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    link_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    link_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    link_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    link_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    link_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether its type was user-selected.")
    link_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    link_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    link_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    link_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")

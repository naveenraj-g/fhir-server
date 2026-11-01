from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import DocumentRelationshipType, IdentifierUse


class DocumentReferenceRelatesToInput(BaseModel):
    """DocumentReference.relatesTo entry."""

    model_config = ConfigDict(extra="forbid")
    code: DocumentRelationshipType = Field(
        ..., description="replaces | transforms | signs | appends"
    )
    target: str | None = Field(
        None, description="Target of the relationship (e.g. 'DocumentReference/320000')."
    )
    target_display: str | None = Field(
        None, description="Display text for the target document reference."
    )
    target_identifier_use: IdentifierUse | None = Field(None)
    target_identifier_type_system: str | None = Field(None)
    target_identifier_type_version: str | None = Field(None)
    target_identifier_type_code: str | None = Field(None)
    target_identifier_type_display: str | None = Field(None)
    target_identifier_type_user_selected: bool | None = Field(None)
    target_identifier_type_text: str | None = Field(None)
    target_identifier_system: str | None = Field(None)
    target_identifier_value: str | None = Field(None)
    target_identifier_period_start: datetime | None = Field(None)
    target_identifier_period_end: datetime | None = Field(None)

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse

from .codeable_concept import PlainDetectedIssueCodeableConcept


class PlainDetectedIssueIdentifier(BaseModel):
    """Plain snake_case response shape for DetectedIssue.identifier."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID of identifier.")
    use: IdentifierUse | None = Field(None, description="usual | official | temp | secondary | old.")
    type: PlainDetectedIssueCodeableConcept | None = Field(None, description="Description of identifier.")
    system: str | None = Field(None, description="The namespace for the identifier value.")
    value: str | None = Field(None, description="The value that is unique.")
    period_start: datetime | None = Field(None, description="Time period when id is/was valid (start).")
    period_end: datetime | None = Field(None, description="Time period when id is/was valid (end).")

    assigner_reference: str | None = Field(None, description="Reference to assigner Organization.")
    assigner_type: str | None = Field(None, description="Assigner resource type.")
    assigner_id: int | None = Field(None, description="Assigner public sequence ID.")
    assigner_display: str | None = Field(None, description="Assigner organization display.")

    assigner_identifier_use: IdentifierUse | None = Field(None, description="Fallback assigner identifier use.")
    assigner_identifier_type_system: str | None = Field(None, description="Fallback assigner identifier type system.")
    assigner_identifier_type_version: str | None = Field(None, description="Fallback assigner identifier type version.")
    assigner_identifier_type_code: str | None = Field(None, description="Fallback assigner identifier type code.")
    assigner_identifier_type_display: str | None = Field(None, description="Fallback assigner identifier type display.")
    assigner_identifier_type_user_selected: bool | None = Field(None, description="Fallback assigner identifier type user selected.")
    assigner_identifier_type_text: str | None = Field(None, description="Fallback assigner identifier type text.")
    assigner_identifier_system: str | None = Field(None, description="Fallback assigner identifier system.")
    assigner_identifier_value: str | None = Field(None, description="Fallback assigner identifier value.")
    assigner_identifier_period_start: datetime | None = Field(None, description="Fallback assigner identifier period start.")
    assigner_identifier_period_end: datetime | None = Field(None, description="Fallback assigner identifier period end.")

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse
from app.schemas.risk_assessment.input.codeable_concept import (
    RiskAssessmentCodeableConceptInput,
)


class RiskAssessmentIdentifierInput(BaseModel):
    """FHIR R4 Identifier input for RiskAssessment.identifier."""

    model_config = ConfigDict(extra="forbid")

    use: IdentifierUse | None = Field(None, description="usual | official | temp | secondary | old.")
    type: RiskAssessmentCodeableConceptInput | None = Field(None, description="Description of identifier.")
    system: str | None = Field(None, description="The namespace for the identifier value.")
    value: str | None = Field(None, description="The value that is unique.")
    period_start: datetime | None = Field(None, description="Time period during which identifier is valid — start.")
    period_end: datetime | None = Field(None, description="Time period during which identifier is valid — end.")

    assigner: str | None = Field(None, description="Organization that issued id. Reference(Organization), e.g. 'Organization/190001'.")
    assigner_display: str | None = Field(None, description="Display text for assigner organization.")
    assigner_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — its purpose, if known.")
    assigner_identifier_type_system: str | None = Field(None, description="Fallback identifier — code system for its type.")
    assigner_identifier_type_version: str | None = Field(None, description="Fallback identifier — version of the type code system.")
    assigner_identifier_type_code: str | None = Field(None, description="Fallback identifier — a symbol for its type.")
    assigner_identifier_type_display: str | None = Field(None, description="Fallback identifier — display for its type.")
    assigner_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — whether chosen directly by user.")
    assigner_identifier_type_text: str | None = Field(None, description="Fallback identifier — human language rendering of its type.")
    assigner_identifier_system: str | None = Field(None, description="Fallback identifier — namespace URL for the value.")
    assigner_identifier_value: str | None = Field(None, description="Fallback identifier — value within the given system.")
    assigner_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — start of validity period.")
    assigner_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — end of validity period.")

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse
from app.schemas.risk_assessment.response.codeable_concept import (
    PlainRiskAssessmentCodeableConcept,
)


class PlainRiskAssessmentIdentifier(BaseModel):
    """Plain snake_case representation for RiskAssessment.identifier."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID.")
    use: IdentifierUse | None = Field(None, description="usual | official | temp | secondary | old.")
    type: PlainRiskAssessmentCodeableConcept | None = Field(None, description="Description of identifier.")
    system: str | None = Field(None, description="The namespace for the identifier value.")
    value: str | None = Field(None, description="The value that is unique.")
    period_start: datetime | None = Field(None, description="Validity period start.")
    period_end: datetime | None = Field(None, description="Validity period end.")

    assigner_reference: str | None = Field(None, description="FHIR reference to assigner.")
    assigner_type: str | None = Field(None, description="Target resource type of assigner.")
    assigner_id: int | None = Field(None, description="Target sequence ID of assigner.")
    assigner_display: str | None = Field(None, description="Display text for assigner.")
    assigner_identifier_use: IdentifierUse | None = Field(None, description="Assigner identifier fallback use.")
    assigner_identifier_type_system: str | None = Field(None, description="Assigner identifier fallback type system.")
    assigner_identifier_type_version: str | None = Field(None, description="Assigner identifier fallback type version.")
    assigner_identifier_type_code: str | None = Field(None, description="Assigner identifier fallback type code.")
    assigner_identifier_type_display: str | None = Field(None, description="Assigner identifier fallback type display.")
    assigner_identifier_type_user_selected: bool | None = Field(None, description="Assigner identifier fallback user selected.")
    assigner_identifier_type_text: str | None = Field(None, description="Assigner identifier fallback type text.")
    assigner_identifier_system: str | None = Field(None, description="Assigner identifier fallback system.")
    assigner_identifier_value: str | None = Field(None, description="Assigner identifier fallback value.")
    assigner_identifier_period_start: datetime | None = Field(None, description="Assigner identifier fallback period start.")
    assigner_identifier_period_end: datetime | None = Field(None, description="Assigner identifier fallback period end.")


class RiskAssessmentIdentifierListItem(PlainRiskAssessmentIdentifier):
    """Sub-resource list item for RiskAssessment identifier."""


class RiskAssessmentIdentifierListResponse(BaseModel):
    """Sub-resource list response for RiskAssessment identifiers."""

    model_config = ConfigDict(extra="forbid")

    data: list[RiskAssessmentIdentifierListItem] = Field(..., description="List of identifiers.")
    total: int = Field(..., description="Total count of identifiers.")

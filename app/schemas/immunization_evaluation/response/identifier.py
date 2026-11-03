from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse
from app.schemas.immunization_evaluation.response.codeable_concept import (
    PlainImmunizationEvaluationCodeableConcept,
)


class PlainImmunizationEvaluationIdentifier(BaseModel):
    """Plain snake_case Identifier response."""

    model_config = ConfigDict(extra="forbid")

    id: int | None = Field(None, description="Identifier record internal ID.")
    use: IdentifierUse | None = Field(None, description="usual | official | temp | secondary | old.")
    type: PlainImmunizationEvaluationCodeableConcept | None = Field(None, description="Description of identifier.")
    system: str | None = Field(None, description="The namespace for the identifier value.")
    value: str | None = Field(None, description="The value that is unique.")
    period_start: datetime | None = Field(None, description="Start of validity period.")
    period_end: datetime | None = Field(None, description="End of validity period.")
    assigner: str | None = Field(None, description="Organization that issued id.")
    assigner_display: str | None = Field(None, description="Display text for assigner organization.")

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

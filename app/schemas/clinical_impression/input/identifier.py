from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse

from .codeable_concept import ClinicalImpressionCodeableConceptInput


class ClinicalImpressionIdentifierInput(BaseModel):
    """ClinicalImpression.identifier input element."""

    model_config = ConfigDict(extra="forbid")

    use: IdentifierUse | None = Field(None, description="usual | official | temp | secondary | old.")
    type: ClinicalImpressionCodeableConceptInput | None = Field(None, description="Description of identifier.")
    system: str | None = Field(None, description="The namespace for the identifier value.")
    value: str | None = Field(None, description="The value that is unique.")
    period_start: datetime | None = Field(None, description="Time period when id is/was valid (start).")
    period_end: datetime | None = Field(None, description="Time period when id is/was valid (end).")
    assigner: str | None = Field(None, description="Organization that issued id, e.g. 'Organization/190001'.")
    assigner_display: str | None = Field(None, description="Display text for the assigner organization.")

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

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.care_plan.input.codeable_concept import (
    CarePlanCodeableConceptInput,
)
from app.schemas.enums import IdentifierUse


class CarePlanIdentifierInput(BaseModel):
    """CarePlan.identifier entry."""

    model_config = ConfigDict(extra="forbid")
    use: IdentifierUse | None = Field(
        None, description="usual | official | temp | secondary | old."
    )
    type: CarePlanCodeableConceptInput | None = Field(
        None, description="Description of identifier."
    )
    system: str | None = Field(
        None, description="The namespace for the identifier value."
    )
    value: str | None = Field(
        None, description="The value that is unique within the system."
    )
    period_start: datetime | None = Field(
        None, description="Start of the identifier's validity period."
    )
    period_end: datetime | None = Field(
        None, description="End of the identifier's validity period."
    )
    assigner: str | None = Field(
        None,
        description="Organization that issued/manages the identifier (e.g. 'Organization/190001').",
    )
    assigner_display: str | None = Field(
        None, description="Display name of assigning organization."
    )
    # Assigner logical identifier fallback
    assigner_identifier_use: IdentifierUse | None = Field(
        None, description="Use of assigner identifier."
    )
    assigner_identifier_system: str | None = Field(
        None, description="System for assigner identifier."
    )
    assigner_identifier_value: str | None = Field(
        None, description="Value for assigner identifier."
    )
    assigner_identifier_type_text: str | None = Field(
        None, description="Type text for assigner identifier."
    )

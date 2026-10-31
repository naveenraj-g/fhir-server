from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.allergy_intolerance.input.codeable_concept import (
    AllergyIntoleranceCodeableConceptInput,
)


class AllergyIntoleranceIdentifierInput(BaseModel):
    """Identifier input for AllergyIntolerance."""

    model_config = ConfigDict(extra="forbid")

    use: str | None = Field(
        None, description="usual | official | temp | secondary | old."
    )
    type: AllergyIntoleranceCodeableConceptInput | None = Field(
        None, description="Description of identifier."
    )
    system: str | None = Field(
        None, description="The namespace for the identifier value."
    )
    value: str | None = Field(None, description="The value that is unique.")
    period_start: datetime | None = Field(
        None, description="Time period during which identifier is valid (start)."
    )
    period_end: datetime | None = Field(
        None, description="Time period during which identifier is valid (end)."
    )
    assigner: str | None = Field(
        None, description="Organization that issued id. Reference(Organization)"
    )
    assigner_display: str | None = Field(
        None, description="Display text for assigner."
    )

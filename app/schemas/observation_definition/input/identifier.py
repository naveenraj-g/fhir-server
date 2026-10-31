from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse

from .codeable_concept import ObservationDefinitionCodeableConceptInput


class ObservationDefinitionIdentifierInput(BaseModel):
    """ObservationDefinition.identifier (0..*) input schema."""

    model_config = ConfigDict(extra="forbid")

    use: IdentifierUse | None = Field(
        None, description="usual | official | temp | secondary | old"
    )
    type: ObservationDefinitionCodeableConceptInput | None = Field(
        None, description="Description of identifier."
    )
    system: str | None = Field(
        None, description="The namespace for the identifier value."
    )
    value: str | None = Field(None, description="The value that is unique.")
    period_start: datetime | None = Field(
        None, description="Time period when id is/was valid for use."
    )
    period_end: datetime | None = Field(
        None, description="Time period when id is/was valid for use."
    )
    assigner: str | None = Field(
        None,
        description="Organization that issued id (e.g. Organization/190001).",
    )
    assigner_display: str | None = Field(
        None, description="Display name for assigner organization."
    )

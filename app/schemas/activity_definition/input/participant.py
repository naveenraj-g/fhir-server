from pydantic import BaseModel, ConfigDict, Field

from app.models.activity_definition.enums import ActivityDefinitionParticipantType
from app.schemas.activity_definition.input.codeable_concept import (
    ActivityDefinitionCodeableConceptInput,
)


class ActivityDefinitionParticipantInput(BaseModel):
    """ActivityDefinition.participant input schema."""

    model_config = ConfigDict(extra="forbid")

    type: ActivityDefinitionParticipantType = Field(
        ...,
        description="patient | practitioner | related-person | device.",
    )
    role: ActivityDefinitionCodeableConceptInput | None = Field(
        None, description="Role of participant in activity."
    )

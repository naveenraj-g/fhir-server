from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.task.input.reference import TaskReferenceInput


class TaskRestrictionInput(BaseModel):
    """Constraints on task execution."""

    model_config = ConfigDict(extra="forbid")

    repetitions: int | None = Field(
        None, description="How many times to repeat."
    )
    period_start: datetime | None = Field(
        None, description="When fulfillment is permitted — start."
    )
    period_end: datetime | None = Field(
        None, description="When fulfillment is permitted — end."
    )
    recipient: list[TaskReferenceInput | str] | None = Field(
        None, description="For whom is task expected to be executed (Reference(Patient|Practitioner|PractitionerRole|RelatedPerson|Group|Organization))."
    )

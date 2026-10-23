from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class ScheduleServiceCategoryInput(BaseModel):
    """Schedule.serviceCategory — high-level category of service being
    performed (CodeableConcept). `text` is the CodeableConcept's own field
    (sibling of coding[], not part of it); `coding` is the real 0..* list."""

    model_config = ConfigDict(extra="forbid")
    coding: list[CodingInput] | None = Field(
        None,
        description="Coding(s) for this service category — may include both a custom code and a standard-terminology crosswalk.",
    )
    text: str | None = Field(
        None,
        description="A human language representation of the category, as seen/selected/entered by the user.",
    )

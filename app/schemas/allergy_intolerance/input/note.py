from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AllergyIntoleranceNoteInput(BaseModel):
    """Note/Annotation input for AllergyIntolerance."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., description="The annotation content as text.")
    time: datetime | None = Field(
        None, description="When the annotation was made."
    )
    author_string: str | None = Field(
        None, description="Individual responsible for the annotation (string)."
    )
    author_reference: str | None = Field(
        None,
        description="Individual responsible for the annotation. Reference(Practitioner|PractitionerRole|Patient|RelatedPerson)",
    )
    author_reference_display: str | None = Field(
        None, description="Display text for author reference."
    )

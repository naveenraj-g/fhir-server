from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.allergy_intolerance.enums import AllergyIntoleranceSeverity
from app.schemas.allergy_intolerance.input.codeable_concept import (
    AllergyIntoleranceCodeableConceptInput,
)
from app.schemas.allergy_intolerance.input.note import (
    AllergyIntoleranceNoteInput,
)


class AllergyIntoleranceReactionInput(BaseModel):
    """Reaction component input for AllergyIntolerance."""

    model_config = ConfigDict(extra="forbid")

    substance: AllergyIntoleranceCodeableConceptInput | None = Field(
        None, description="Specific substance or pharmaceutical product considered responsible."
    )
    manifestation: list[AllergyIntoleranceCodeableConceptInput] = Field(
        ...,
        min_length=1,
        description="Clinical symptoms/signs associated with the Event (1..*).",
    )
    description: str | None = Field(
        None, description="Description of the event as a whole."
    )
    onset: datetime | None = Field(
        None, description="Date(/time) when manifestations showed."
    )
    severity: AllergyIntoleranceSeverity | None = Field(
        None, description="mild | moderate | severe (of event as a whole)."
    )
    exposure_route: AllergyIntoleranceCodeableConceptInput | None = Field(
        None, description="How the subject was exposed to the substance."
    )
    note: list[AllergyIntoleranceNoteInput] | None = Field(
        None, description="Text about event not captured in other fields."
    )

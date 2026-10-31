from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .codeable_concept import SpecimenCodeableConceptInput
from .reference import SpecimenAdditiveReferenceInput


class SpecimenProcessingInput(BaseModel):
    """Specimen.processing (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    description: str | None = Field(
        None, description="Textual description of procedure."
    )
    procedure: SpecimenCodeableConceptInput | None = Field(
        None, description="Indicates the mechanism used by the specimen processing step."
    )
    additive: list[SpecimenAdditiveReferenceInput] | None = Field(
        None, description="Material used in the processing step (Reference(Substance))."
    )
    time_date_time: datetime | None = Field(
        None, description="Date and time of specimen processing."
    )
    time_period_start: datetime | None = Field(
        None, description="Start of specimen processing period."
    )
    time_period_end: datetime | None = Field(
        None, description="End of specimen processing period."
    )

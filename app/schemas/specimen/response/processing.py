from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRCodeableConcept, FHIRPeriod, FHIRReference

from .codeable_concept import PlainSpecimenCodeableConcept
from .reference import PlainSpecimenReference


class FHIRSpecimenProcessing(BaseModel):
    """FHIR representation of Specimen.processing."""

    description: str | None = Field(None, description="Textual description of procedure.")
    procedure: FHIRCodeableConcept | None = Field(None, description="Indicates the mechanism used.")
    additive: list[FHIRReference] | None = Field(None, description="Material used in the processing step.")
    timeDateTime: str | None = Field(None, description="Date and time of processing.")
    timePeriod: FHIRPeriod | None = Field(None, description="Period of processing.")


class PlainSpecimenProcessing(BaseModel):
    """Plain response representation of Specimen.processing."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal DB ID.")
    description: str | None = Field(None, description="Textual description of procedure.")
    procedure: PlainSpecimenCodeableConcept | None = Field(None, description="Procedure concept.")
    additive: list[PlainSpecimenReference] | None = Field(None, description="Material used in the processing step.")
    time_date_time: str | None = Field(None, description="Date and time of processing.")
    time_period_start: str | None = Field(None, description="Start of processing period.")
    time_period_end: str | None = Field(None, description="End of processing period.")

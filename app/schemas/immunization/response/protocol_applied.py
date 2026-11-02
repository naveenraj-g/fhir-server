from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRCodeableConcept, FHIRReference
from app.schemas.immunization.response.codeable_concept import (
    PlainImmunizationCodeableConcept,
)
from app.schemas.immunization.response.reference import (
    PlainImmunizationReference,
)


class FHIRImmunizationProtocolApplied(BaseModel):
    model_config = ConfigDict(extra="allow")

    series: str | None = Field(None, description="Name of vaccine series.")
    authority: FHIRReference | None = Field(None, description="Who is responsible for publishing the recommendations.")
    targetDisease: list[FHIRCodeableConcept] | None = Field(None, description="Vaccine preventatable disease being targetted.")
    doseNumberPositiveInt: int | None = Field(None, description="Nominal position in a series as integer.")
    doseNumberString: str | None = Field(None, description="Nominal position in a series as string.")
    seriesDosesPositiveInt: int | None = Field(None, description="Recommended number of doses for immunity as integer.")
    seriesDosesString: str | None = Field(None, description="Recommended number of doses for immunity as string.")


class PlainImmunizationProtocolApplied(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID.")
    series: str | None = Field(None, description="Name of vaccine series.")
    authority: PlainImmunizationReference | None = Field(None, description="Who is responsible for publishing the recommendations.")
    target_disease: list[PlainImmunizationCodeableConcept] | None = Field(None, description="Vaccine preventatable disease being targetted.")
    dose_number_positive_int: int | None = Field(None, description="Dose number within series as integer.")
    dose_number_string: str | None = Field(None, description="Dose number within series as string.")
    series_doses_positive_int: int | None = Field(None, description="Recommended number of doses for immunity as integer.")
    series_doses_string: str | None = Field(None, description="Recommended number of doses for immunity as string.")

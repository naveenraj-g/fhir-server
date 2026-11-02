from pydantic import BaseModel, ConfigDict, Field

from app.schemas.immunization.input.codeable_concept import (
    ImmunizationCodeableConceptInput,
)
from app.schemas.immunization.input.reference import ImmunizationAuthorityInput


class ImmunizationProtocolAppliedInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    series: str | None = Field(None, description="Name of vaccine series.")
    authority: ImmunizationAuthorityInput | None = Field(
        None, description="Who is responsible for publishing the recommendations (Reference(Organization))."
    )
    target_disease: list[ImmunizationCodeableConceptInput] | None = Field(
        None, description="Vaccine preventatable disease being targetted."
    )
    dose_number_positive_int: int | None = Field(None, description="Dose number within series as integer.")
    dose_number_string: str | None = Field(None, description="Dose number within series as string.")
    series_doses_positive_int: int | None = Field(None, description="Recommended number of doses for immunity as integer.")
    series_doses_string: str | None = Field(None, description="Recommended number of doses for immunity as string.")

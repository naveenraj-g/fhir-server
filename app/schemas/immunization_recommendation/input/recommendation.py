from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.immunization_recommendation.input.codeable_concept import (
    ImmunizationRecommendationCodeableConceptInput,
)
from app.schemas.immunization_recommendation.input.reference import (
    ImmunizationRecommendationSupportingImmunizationInput,
    ImmunizationRecommendationSupportingPatientInfoInput,
)


class ImmunizationRecommendationDateCriterionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: ImmunizationRecommendationCodeableConceptInput = Field(
        ..., description="Type of date, e.g. recommended | earliest | overdue."
    )
    value: datetime = Field(..., description="Recommended date.")


class ImmunizationRecommendationRecommendationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    vaccine_code: list[ImmunizationRecommendationCodeableConceptInput] | None = Field(
        None, description="Vaccine  or vaccine group recommendation applies to."
    )
    target_disease: ImmunizationRecommendationCodeableConceptInput | None = Field(
        None, description="Disease to be immunized against."
    )
    contraindicated_vaccine_code: list[ImmunizationRecommendationCodeableConceptInput] | None = Field(
        None, description="Vaccine which is contraindicated to fulfill the recommendation."
    )
    forecast_status: ImmunizationRecommendationCodeableConceptInput = Field(
        ..., description="Vaccine recommendation status, e.g. due | overdue."
    )
    forecast_reason: list[ImmunizationRecommendationCodeableConceptInput] | None = Field(
        None, description="Reason for the recommendation."
    )
    date_criterion: list[ImmunizationRecommendationDateCriterionInput] | None = Field(
        None, description="Dates governing proposed immunization."
    )
    description: str | None = Field(None, description="Protocol details.")
    series: str | None = Field(None, description="Name of vaccination series.")
    dose_number_positive_int: int | None = Field(None, description="Recommended dose number in series (positive integer).")
    dose_number_string: str | None = Field(None, description="Recommended dose number in series (string).")
    series_doses_positive_int: int | None = Field(None, description="Recommended number of doses for series (positive integer).")
    series_doses_string: str | None = Field(None, description="Recommended number of doses for series (string).")
    supporting_immunization: list[ImmunizationRecommendationSupportingImmunizationInput] | None = Field(
        None, description="Past immunizations supporting recommendation."
    )
    supporting_patient_information: list[ImmunizationRecommendationSupportingPatientInfoInput] | None = Field(
        None, description="Patient observations supporting recommendation."
    )

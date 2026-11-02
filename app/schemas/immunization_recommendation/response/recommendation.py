from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import FHIRCodeableConcept, FHIRReference
from app.schemas.immunization_recommendation.response.codeable_concept import (
    PlainImmunizationRecommendationCodeableConcept,
)
from app.schemas.immunization_recommendation.response.reference import (
    PlainImmunizationRecommendationReference,
)


class FHIRImmunizationRecommendationDateCriterion(BaseModel):
    model_config = ConfigDict(extra="allow")

    code: FHIRCodeableConcept = Field(..., description="Type of date.")
    value: str = Field(..., description="Recommended date.")


class FHIRImmunizationRecommendationRecommendation(BaseModel):
    model_config = ConfigDict(extra="allow")

    vaccineCode: list[FHIRCodeableConcept] | None = Field(None, description="Vaccine recommendation applies to.")
    targetDisease: FHIRCodeableConcept | None = Field(None, description="Disease to be immunized against.")
    contraindicatedVaccineCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Vaccine which is contraindicated."
    )
    forecastStatus: FHIRCodeableConcept = Field(..., description="Vaccine recommendation status.")
    forecastReason: list[FHIRCodeableConcept] | None = Field(None, description="Reason for the recommendation.")
    dateCriterion: list[FHIRImmunizationRecommendationDateCriterion] | None = Field(
        None, description="Dates governing proposed immunization."
    )
    description: str | None = Field(None, description="Protocol details.")
    series: str | None = Field(None, description="Name of vaccination series.")
    doseNumberPositiveInt: int | None = Field(None, description="Recommended dose number in series.")
    doseNumberString: str | None = Field(None, description="Recommended dose number in series.")
    seriesDosesPositiveInt: int | None = Field(None, description="Recommended number of doses for series.")
    seriesDosesString: str | None = Field(None, description="Recommended number of doses for series.")
    supportingImmunization: list[FHIRReference] | None = Field(
        None, description="Past immunizations supporting recommendation."
    )
    supportingPatientInformation: list[FHIRReference] | None = Field(
        None, description="Patient observations supporting recommendation."
    )


class PlainImmunizationRecommendationDateCriterion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = Field(None, description="Internal DB ID of date criterion row.")
    code: PlainImmunizationRecommendationCodeableConcept = Field(..., description="Type of date.")
    value: datetime = Field(..., description="Recommended date.")


class PlainImmunizationRecommendationRecommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int | None = Field(None, description="Internal DB ID of recommendation row.")
    vaccine_code: list[PlainImmunizationRecommendationCodeableConcept] | None = Field(
        None, description="Vaccine recommendation applies to."
    )
    target_disease: PlainImmunizationRecommendationCodeableConcept | None = Field(
        None, description="Disease to be immunized against."
    )
    contraindicated_vaccine_code: list[PlainImmunizationRecommendationCodeableConcept] | None = Field(
        None, description="Vaccine which is contraindicated."
    )
    forecast_status: PlainImmunizationRecommendationCodeableConcept = Field(
        ..., description="Vaccine recommendation status."
    )
    forecast_reason: list[PlainImmunizationRecommendationCodeableConcept] | None = Field(
        None, description="Reason for the recommendation."
    )
    date_criterion: list[PlainImmunizationRecommendationDateCriterion] | None = Field(
        None, description="Dates governing proposed immunization."
    )
    description: str | None = Field(None, description="Protocol details.")
    series: str | None = Field(None, description="Name of vaccination series.")
    dose_number_positive_int: int | None = Field(None, description="Recommended dose number in series.")
    dose_number_string: str | None = Field(None, description="Recommended dose number in series.")
    series_doses_positive_int: int | None = Field(None, description="Recommended number of doses for series.")
    series_doses_string: str | None = Field(None, description="Recommended number of doses for series.")
    supporting_immunization: list[PlainImmunizationRecommendationReference] | None = Field(
        None, description="Past immunizations supporting recommendation."
    )
    supporting_patient_information: list[PlainImmunizationRecommendationReference] | None = Field(
        None, description="Patient observations supporting recommendation."
    )

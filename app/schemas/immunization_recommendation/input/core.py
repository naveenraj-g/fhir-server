from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.immunization_recommendation.input.identifier import (
    ImmunizationRecommendationIdentifierInput,
)
from app.schemas.immunization_recommendation.input.recommendation import (
    ImmunizationRecommendationRecommendationInput,
)
from app.schemas.immunization_recommendation.input.reference import (
    ImmunizationRecommendationAuthorityInput,
    ImmunizationRecommendationPatientInput,
)

_CREATE_EXAMPLE: dict[str, Any] = {
    "patient": {
        "reference": "Patient/10001",
        "reference_display": "Jane Doe",
    },
    "date": "2026-02-01T10:00:00Z",
    "authority": {
        "reference": "Organization/190001",
        "reference_display": "National Health Authority",
    },
    "recommendation": [
        {
            "vaccine_code": [
                {
                    "coding": [
                        {
                            "system": "http://hl7.org/fhir/sid/cvx",
                            "code": "197",
                            "display": "influenza, high-dose, quadrivalent",
                        }
                    ],
                    "text": "Fluzone High-Dose Quadrivalent",
                }
            ],
            "target_disease": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "6142004",
                        "display": "Influenza",
                    }
                ],
                "text": "Influenza",
            },
            "forecast_status": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/immunization-recommendation-status",
                        "code": "due",
                        "display": "Due",
                    }
                ],
                "text": "Due",
            },
            "date_criterion": [
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "30980-7",
                                "display": "Date vaccine due",
                            }
                        ],
                        "text": "Date vaccine due",
                    },
                    "value": "2026-02-15T00:00:00Z",
                }
            ],
            "description": "Annual influenza vaccination recommended for older adults.",
            "series": "Annual",
            "dose_number_positive_int": 1,
            "series_doses_positive_int": 1,
        }
    ],
}


class ImmunizationRecommendationCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _CREATE_EXAMPLE},
    )

    patient: ImmunizationRecommendationPatientInput = Field(
        ..., description="Who this profile is for (Reference(Patient))."
    )
    date: datetime = Field(
        ..., description="Date the recommendation was generated."
    )
    authority: ImmunizationRecommendationAuthorityInput | None = Field(
        None, description="Who is responsible for protocol (Reference(Organization))."
    )
    identifier: list[ImmunizationRecommendationIdentifierInput] | None = Field(
        None, description="Business identifier."
    )
    recommendation: list[ImmunizationRecommendationRecommendationInput] = Field(
        ..., min_length=1, description="Vaccine administration recommendations."
    )


class ImmunizationRecommendationPatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient: ImmunizationRecommendationPatientInput | None = Field(
        None, description="Who this profile is for (Reference(Patient))."
    )
    date: datetime | None = Field(
        None, description="Date the recommendation was generated."
    )
    authority: ImmunizationRecommendationAuthorityInput | None = Field(
        None, description="Who is responsible for protocol (Reference(Organization))."
    )
    identifier: list[ImmunizationRecommendationIdentifierInput] | None = Field(
        None, description="Business identifier."
    )
    recommendation: list[ImmunizationRecommendationRecommendationInput] | None = Field(
        None, description="Vaccine administration recommendations."
    )

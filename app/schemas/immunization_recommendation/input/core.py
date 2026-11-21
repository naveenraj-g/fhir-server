from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirReferenceInput,
)

_EXAMPLE = {
    "resourceType": "ImmunizationRecommendation",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/immunization-recommendation-id",
            "value": "IR-1001",
        }
    ],
    "patient": {"reference": "Patient/10001"},
    "date": "2023-01-15T09:30:00Z",
    "authority": {"reference": "Organization/190001"},
    "recommendation": [
        {
            "vaccineCode": [
                {
                    "coding": [
                        {
                            "system": "http://hl7.org/fhir/sid/cvx",
                            "code": "140",
                            "display": "Influenza, seasonal, injectable, preservative free",
                        }
                    ]
                }
            ],
            "targetDisease": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "6142004",
                        "display": "Influenza",
                    }
                ]
            },
            "forecastStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/immunization-recommendation-status",
                        "code": "due",
                        "display": "Due",
                    }
                ]
            },
            "dateCriterion": [
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "30980-7",
                                "display": "Date vaccine due",
                            }
                        ]
                    },
                    "value": "2023-06-01T00:00:00Z",
                }
            ],
            "series": "Seasonal",
            "doseNumberPositiveInt": 1,
            "seriesDosesPositiveInt": 1,
            "supportingImmunization": [{"reference": "Immunization/330001"}],
        }
    ],
}


class ImmunizationRecommendationDateCriterionInput(FhirInputModel):
    """ImmunizationRecommendation.recommendation.dateCriterion — a date that governs the proposed immunization."""

    code: FhirCodeableConceptInput | None = Field(
        None, description="Type of date (required by R4)."
    )
    value: str | None = Field(
        None, description="Recommended date (a FHIR dateTime; required by R4)."
    )


class ImmunizationRecommendationRecommendationInput(FhirInputModel):
    """ImmunizationRecommendation.recommendation — one vaccine administration recommendation."""

    vaccineCode: list[FhirCodeableConceptInput] | None = Field(
        None,
        description="Vaccine or vaccine group the recommendation applies to (rule imr-1: one of vaccineCode or targetDisease is required).",
    )
    targetDisease: FhirCodeableConceptInput | None = Field(
        None, description="Disease to be immunized against."
    )
    contraindicatedVaccineCode: list[FhirCodeableConceptInput] | None = Field(
        None,
        description="Vaccine which is contraindicated to fulfill the recommendation.",
    )
    forecastStatus: FhirCodeableConceptInput | None = Field(
        None, description="Vaccine recommendation status (required by R4)."
    )
    forecastReason: list[FhirCodeableConceptInput] | None = Field(
        None, description="Vaccine administration status reason."
    )
    dateCriterion: list[ImmunizationRecommendationDateCriterionInput] | None = Field(
        None, description="Dates governing the proposed immunization."
    )
    description: str | None = Field(None, description="Protocol details.")
    series: str | None = Field(None, description="Name of the vaccination series.")
    doseNumberPositiveInt: int | None = Field(
        None,
        description="Recommended dose number within the series (a positiveInt). One of the doseNumber[x] choices.",
    )
    doseNumberString: str | None = Field(
        None,
        description="Recommended dose number within the series (a string). One of the doseNumber[x] choices.",
    )
    seriesDosesPositiveInt: int | None = Field(
        None,
        description="Recommended number of doses for immunity (a positiveInt). One of the seriesDoses[x] choices.",
    )
    seriesDosesString: str | None = Field(
        None,
        description="Recommended number of doses for immunity (a string). One of the seriesDoses[x] choices.",
    )
    supportingImmunization: list[FhirReferenceInput] | None = Field(
        None,
        description="Past immunizations supporting the recommendation — Reference(Immunization | ImmunizationEvaluation). A relative Immunization reference must exist in the caller's org (422 otherwise).",
    )
    supportingPatientInformation: list[FhirReferenceInput] | None = Field(
        None,
        description="Patient observations supporting the recommendation — Reference(Any). A relative reference to a resource on this server (Condition, Procedure, ...) must exist in the caller's org (422 otherwise).",
    )


class _ImmunizationRecommendationFields(FhirInputModel):
    """Every writable ImmunizationRecommendation element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/immunizationrecommendation.html). Create and patch accept
    exactly the same fields. R4 requires `patient`, `date` and `recommendation` (1..*); that
    is enforced by base R4 validation of the stored document (the `java_validator` backend —
    the native structural check has no cardinality minimums), not by this model. A PATCH may
    omit them: it is merged onto the current resource before validating.

    The validated body is stored whole (ImmunizationRecommendationModel.content), so any valid
    R4 element is kept — including ones this model does not declare. Server-managed
    elements are ignored if sent: `id` (assigned from the immunization_recommendation_id
    sequence) and `meta` (audit/tenant data, stamped on at read time). org_id and
    created_by/updated_by come from the verified JWT (actor.org_id / actor.sub),
    never the body. There is no user_id."""

    resourceType: Literal["ImmunizationRecommendation"] | None = Field(
        None,
        description="Optional; if supplied it must be 'ImmunizationRecommendation'.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Business identifier."
    )
    patient: FhirReferenceInput | None = Field(
        None,
        description="Who this profile is for — Reference(Patient) (required by R4). A relative 'Patient/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    date: str | None = Field(
        None,
        description="Date the recommendation(s) were created (a FHIR dateTime; required by R4).",
    )
    authority: FhirReferenceInput | None = Field(
        None,
        description="Who is responsible for the protocol — Reference(Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    recommendation: list[ImmunizationRecommendationRecommendationInput] | None = Field(
        None,
        description="Vaccine administration recommendations (at least one, required by R4).",
    )


class ImmunizationRecommendationCreateSchema(_ImmunizationRecommendationFields):
    """POST body — a FHIR R4 ImmunizationRecommendation resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class ImmunizationRecommendationPatchSchema(_ImmunizationRecommendationFields):
    """PATCH body — a partial FHIR R4 ImmunizationRecommendation (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones are left
    untouched. A supplied element replaces the stored value wholesale — a list
    (even `[]`) replaces every existing entry, an object such as `patient` replaces
    the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "date": "2023-02-01T00:00:00Z",
                "authority": {"reference": "Organization/190001"},
            }
        }
    }

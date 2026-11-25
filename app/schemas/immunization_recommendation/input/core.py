"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.immunization_recommendation import (
    ImmunizationRecommendation,
    ImmunizationRecommendationPatch,
)

_CREATE_EXAMPLE = {
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
                            "display": "Influenza, seasonal, "
                            "injectable, preservative "
                            "free",
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

_PATCH_EXAMPLE = {
    "date": "2023-02-01T00:00:00Z",
    "authority": {"reference": "Organization/190001"},
}


class ImmunizationRecommendationCreateSchema(ImmunizationRecommendation):
    "POST body - a FHIR R4 ImmunizationRecommendation resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class ImmunizationRecommendationPatchSchema(ImmunizationRecommendationPatch):
    "PATCH body - a partial FHIR R4 ImmunizationRecommendation (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

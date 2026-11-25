"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.risk_assessment import (
    RiskAssessment,
    RiskAssessmentPatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "RiskAssessment",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/risk-assessment-id",
            "value": "RA-1001",
        }
    ],
    "status": "final",
    "method": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "225338004",
                "display": "Risk assessment",
            }
        ]
    },
    "code": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "709510001",
                "display": "Assessment of risk for cardiovascular disease",
            }
        ]
    },
    "subject": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "occurrenceDateTime": "2023-01-15T09:30:00Z",
    "condition": {"reference": "Condition/120001"},
    "performer": {"reference": "Practitioner/30001"},
    "reasonCode": [{"text": "Family history of heart disease"}],
    "prediction": [
        {
            "outcome": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "54329005",
                        "display": "Acute myocardial infarction",
                    }
                ]
            },
            "probabilityDecimal": 12.5,
            "qualitativeRisk": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/risk-probability",
                        "code": "moderate",
                        "display": "moderate likelihood",
                    }
                ]
            },
            "relativeRisk": 1.4,
            "whenRange": {
                "low": {
                    "value": 40,
                    "unit": "yr",
                    "system": "http://unitsofmeasure.org",
                    "code": "a",
                },
                "high": {
                    "value": 50,
                    "unit": "yr",
                    "system": "http://unitsofmeasure.org",
                    "code": "a",
                },
            },
            "rationale": "Based on lipid panel and blood pressure.",
        }
    ],
    "mitigation": "Statin therapy and lifestyle changes.",
    "note": [{"text": "Reassess in 12 months."}],
}

_PATCH_EXAMPLE = {
    "status": "amended",
    "mitigation": "Statin therapy, lifestyle changes and a blood-pressure check.",
}


class RiskAssessmentCreateSchema(RiskAssessment):
    "POST body - a FHIR R4 RiskAssessment resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class RiskAssessmentPatchSchema(RiskAssessmentPatch):
    "PATCH body - a partial FHIR R4 RiskAssessment (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

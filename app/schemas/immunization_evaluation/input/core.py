"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.immunization_evaluation import (
    ImmunizationEvaluation,
    ImmunizationEvaluationPatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "ImmunizationEvaluation",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/immunization-evaluation-id",
            "value": "IE-1001",
        }
    ],
    "status": "completed",
    "patient": {"type": "Patient", "display": "Example patient"},
    "date": "2023-01-15T09:30:00Z",
    "authority": {"type": "Organization", "display": "Example organization"},
    "targetDisease": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "6142004",
                "display": "Influenza",
            }
        ]
    },
    "immunizationEvent": {"type": "Immunization", "display": "Example immunization"},
    "doseStatus": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/immunization-evaluation-dose-status",
                "code": "valid",
                "display": "Valid",
            }
        ]
    },
    "doseStatusReason": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/immunization-evaluation-dose-status-reason",
                    "code": "outsidesched",
                    "display": "Administered outside recommended schedule",
                }
            ]
        }
    ],
    "description": "Evaluated against the seasonal flu schedule",
    "series": "Seasonal",
    "doseNumberPositiveInt": 1,
    "seriesDosesPositiveInt": 1,
}

_PATCH_EXAMPLE = {
    "status": "entered-in-error",
    "description": "Evaluated against the wrong schedule.",
}


class ImmunizationEvaluationCreateSchema(ImmunizationEvaluation):
    "POST body - a FHIR R4 ImmunizationEvaluation resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class ImmunizationEvaluationPatchSchema(ImmunizationEvaluationPatch):
    "PATCH body - a partial FHIR R4 ImmunizationEvaluation (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

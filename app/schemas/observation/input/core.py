"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.observation import Observation, ObservationPatch

_CREATE_EXAMPLE = {
    "resourceType": "Observation",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/observation-id",
            "value": "OBS-1001",
        }
    ],
    "status": "final",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "vital-signs",
                    "display": "Vital Signs",
                }
            ]
        }
    ],
    "code": {
        "coding": [
            {
                "system": "http://loinc.org",
                "code": "85354-9",
                "display": "Blood pressure panel",
            }
        ]
    },
    "subject": {"type": "Patient", "display": "Example patient"},
    "encounter": {"type": "Encounter", "display": "Example encounter"},
    "effectiveDateTime": "2023-01-15T09:30:00Z",
    "issued": "2023-01-15T09:35:00Z",
    "performer": [{"type": "Practitioner", "display": "Example practitioner"}],
    "interpretation": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
                    "code": "H",
                }
            ]
        }
    ],
    "component": [
        {
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "8480-6",
                        "display": "Systolic blood pressure",
                    }
                ]
            },
            "valueQuantity": {
                "value": 142,
                "unit": "mmHg",
                "system": "http://unitsofmeasure.org",
                "code": "mm[Hg]",
            },
        },
        {
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "8462-4",
                        "display": "Diastolic blood pressure",
                    }
                ]
            },
            "valueQuantity": {
                "value": 91,
                "unit": "mmHg",
                "system": "http://unitsofmeasure.org",
                "code": "mm[Hg]",
            },
        },
    ],
}

_PATCH_EXAMPLE = {
    "status": "amended",
    "note": [{"text": "Blood pressure re-checked after five minutes of rest."}],
}


class ObservationCreateSchema(Observation):
    "POST body - a FHIR R4 Observation resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class ObservationPatchSchema(ObservationPatch):
    "PATCH body - a partial FHIR R4 Observation (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

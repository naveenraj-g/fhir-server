"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.allergy_intolerance import (
    AllergyIntolerance,
    AllergyIntolerancePatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "AllergyIntolerance",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/allergy-id",
            "value": "AI-1001",
        }
    ],
    "clinicalStatus": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                "code": "active",
            }
        ]
    },
    "verificationStatus": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
                "code": "confirmed",
            }
        ]
    },
    "type": "allergy",
    "category": ["food"],
    "criticality": "high",
    "code": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "227493005",
                "display": "Cashew nuts",
            }
        ]
    },
    "patient": {"type": "Patient", "display": "Example patient"},
    "encounter": {"type": "Encounter", "display": "Example encounter"},
    "onsetDateTime": "2023-01-15T09:30:00Z",
    "recordedDate": "2023-01-15T10:00:00Z",
    "recorder": {"type": "Practitioner", "display": "Example practitioner"},
    "asserter": {"type": "Patient", "display": "Example patient"},
    "lastOccurrence": "2023-06-01T12:00:00Z",
    "note": [
        {
            "text": "Severe urticaria after cashew ingestion.",
            "time": "2023-01-15T10:05:00Z",
        }
    ],
    "reaction": [
        {
            "substance": {
                "coding": [{"system": "http://snomed.info/sct", "code": "227493005"}]
            },
            "manifestation": [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "64305001",
                            "display": "Urticaria",
                        }
                    ]
                }
            ],
            "description": "Severe hives on face and neck",
            "onset": "2023-01-15T09:40:00Z",
            "severity": "severe",
            "exposureRoute": {
                "coding": [{"system": "http://snomed.info/sct", "code": "26643006"}]
            },
        }
    ],
}

_PATCH_EXAMPLE = {
    "criticality": "low",
    "clinicalStatus": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                "code": "resolved",
            }
        ]
    },
}


class AllergyIntoleranceCreateSchema(AllergyIntolerance):
    "POST body - a FHIR R4 AllergyIntolerance resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class AllergyIntolerancePatchSchema(AllergyIntolerancePatch):
    "PATCH body - a partial FHIR R4 AllergyIntolerance (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

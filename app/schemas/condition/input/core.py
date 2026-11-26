"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.condition import Condition, ConditionPatch

_CREATE_EXAMPLE = {
    "resourceType": "Condition",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/condition-id",
            "value": "C-1001",
        }
    ],
    "clinicalStatus": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": "active",
            }
        ]
    },
    "verificationStatus": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                "code": "confirmed",
            }
        ]
    },
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                    "code": "problem-list-item",
                }
            ]
        }
    ],
    "severity": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "24484000",
                "display": "Severe",
            }
        ]
    },
    "code": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "38341003",
                "display": "Hypertension",
            }
        ]
    },
    "bodySite": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "368208006",
                    "display": "Left upper arm",
                }
            ]
        }
    ],
    "subject": {"type": "Patient", "display": "Example patient"},
    "encounter": {"type": "Encounter", "display": "Example encounter"},
    "onsetDateTime": "2023-01-15T09:30:00Z",
    "recordedDate": "2023-01-15T10:00:00Z",
    "recorder": {"type": "Practitioner", "display": "Example practitioner"},
    "asserter": {"type": "Patient", "display": "Example patient"},
    "stage": [
        {
            "summary": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "14803004",
                        "display": "Temporary",
                    }
                ]
            }
        }
    ],
    "evidence": [
        {
            "code": [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "29857009",
                            "display": "Chest pain",
                        }
                    ]
                }
            ],
            "detail": [{"type": "Observation", "display": "Example observation"}],
        }
    ],
    "note": [
        {"text": "Blood pressure poorly controlled.", "time": "2023-01-15T10:05:00Z"}
    ],
}

_PATCH_EXAMPLE = {
    "clinicalStatus": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": "resolved",
            }
        ]
    },
    "abatementDateTime": "2024-05-01",
}


class ConditionCreateSchema(Condition):
    "POST body - a FHIR R4 Condition resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class ConditionPatchSchema(ConditionPatch):
    "PATCH body - a partial FHIR R4 Condition (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

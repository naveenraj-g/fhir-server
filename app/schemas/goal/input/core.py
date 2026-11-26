"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.goal import Goal, GoalPatch

_CREATE_EXAMPLE = {
    "resourceType": "Goal",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/goal-id",
            "value": "G-1",
        }
    ],
    "lifecycleStatus": "active",
    "achievementStatus": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/goal-achievement",
                "code": "in-progress",
            }
        ]
    },
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/goal-category",
                    "code": "dietary",
                }
            ]
        }
    ],
    "priority": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/goal-priority",
                "code": "high-priority",
            }
        ]
    },
    "description": {"text": "Reduce HbA1c below 7%"},
    "subject": {"type": "Patient", "display": "Example patient"},
    "startDate": "2026-01-15",
    "target": [
        {
            "measure": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "4548-4",
                        "display": "Hemoglobin A1c",
                    }
                ]
            },
            "detailQuantity": {"value": 7, "comparator": "<", "unit": "%"},
            "dueDate": "2026-12-31",
        }
    ],
    "statusDate": "2026-01-15",
    "expressedBy": {"type": "Patient", "display": "Example patient"},
    "note": [{"text": "Agreed with the patient."}],
}

_PATCH_EXAMPLE = {
    "lifecycleStatus": "completed",
    "achievementStatus": {"text": "achieved"},
}


class GoalCreateSchema(Goal):
    "POST body - a FHIR R4 Goal resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class GoalPatchSchema(GoalPatch):
    "PATCH body - a partial FHIR R4 Goal (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

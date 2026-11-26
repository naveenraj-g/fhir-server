"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.care_plan import CarePlan, CarePlanPatch

_CREATE_EXAMPLE = {
    "resourceType": "CarePlan",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/care-plan-id",
            "value": "CP-1001",
        }
    ],
    "status": "active",
    "intent": "plan",
    "category": [
        {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
                    "code": "assess-plan",
                }
            ]
        }
    ],
    "title": "Diabetes management plan",
    "subject": {"type": "Patient", "display": "Example patient"},
    "period": {"start": "2026-01-01"},
    "author": {"type": "Practitioner", "display": "Example practitioner"},
    "careTeam": [{"type": "CareTeam", "display": "Example care team"}],
    "addresses": [{"type": "Condition", "display": "Example condition"}],
    "activity": [
        {
            "detail": {
                "kind": "ServiceRequest",
                "code": {
                    "coding": [
                        {"system": "http://snomed.info/sct", "code": "386053000"}
                    ]
                },
                "status": "scheduled",
                "scheduledPeriod": {"start": "2026-02-01", "end": "2026-02-28"},
                "performer": [
                    {"type": "Practitioner", "display": "Example practitioner"}
                ],
            }
        }
    ],
    "note": [{"text": "Review monthly."}],
}

_PATCH_EXAMPLE = {
    "status": "completed",
    "period": {"start": "2026-01-01", "end": "2026-06-30"},
}


class CarePlanCreateSchema(CarePlan):
    "POST body - a FHIR R4 CarePlan resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class CarePlanPatchSchema(CarePlanPatch):
    "PATCH body - a partial FHIR R4 CarePlan (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

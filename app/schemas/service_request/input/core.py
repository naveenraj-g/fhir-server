"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.service_request import (
    ServiceRequest,
    ServiceRequestPatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "ServiceRequest",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/service-request-id",
            "value": "SR-1001",
        }
    ],
    "status": "active",
    "intent": "order",
    "priority": "routine",
    "category": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "108252007",
                    "display": "Laboratory procedure",
                }
            ]
        }
    ],
    "code": {
        "coding": [
            {
                "system": "http://loinc.org",
                "code": "58410-2",
                "display": "CBC panel - Blood by Automated count",
            }
        ]
    },
    "subject": {"type": "Patient", "display": "Example patient"},
    "encounter": {"type": "Encounter", "display": "Example encounter"},
    "occurrenceDateTime": "2023-01-16T09:00:00Z",
    "authoredOn": "2023-01-15T09:30:00Z",
    "requester": {"type": "Practitioner", "display": "Example practitioner"},
    "performer": [{"type": "Organization", "display": "Example organization"}],
    "reasonCode": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "271737000",
                    "display": "Anemia",
                }
            ]
        }
    ],
    "note": [{"text": "Fasting not required."}],
}

_PATCH_EXAMPLE = {
    "status": "completed",
    "priority": "urgent",
    "note": [{"text": "Results called through."}],
}


class ServiceRequestCreateSchema(ServiceRequest):
    "POST body - a FHIR R4 ServiceRequest resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class ServiceRequestPatchSchema(ServiceRequestPatch):
    "PATCH body - a partial FHIR R4 ServiceRequest (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

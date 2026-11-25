"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.healthcare_service import (
    HealthcareService,
    HealthcareServicePatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "HealthcareService",
    "active": True,
    "name": "Cardiology Clinic",
    "providedBy": {"reference": "Organization/190001", "display": "General Hospital"},
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/service-id",
            "value": "SVC-1",
        }
    ],
    "category": [{"coding": [{"code": "35", "display": "Specialist Medical"}]}],
    "type": [{"coding": [{"code": "124", "display": "General Practice"}]}],
    "specialty": [{"coding": [{"code": "394579002", "display": "Cardiology"}]}],
    "location": [{"reference": "Location/230001"}],
    "coverageArea": [{"reference": "Location/230002"}],
    "comment": "Heart-health clinic.",
    "telecom": [{"system": "phone", "value": "555-1234", "use": "work"}],
    "appointmentRequired": True,
    "availableTime": [
        {
            "daysOfWeek": ["mon", "tue", "wed"],
            "availableStartTime": "08:00:00",
            "availableEndTime": "17:00:00",
        }
    ],
    "notAvailable": [
        {
            "description": "Closed for the holidays",
            "during": {"start": "2026-12-24T00:00:00Z", "end": "2026-12-26T00:00:00Z"},
        }
    ],
    "endpoint": [
        {
            "identifier": {
                "system": "https://fhir-server.dev/fhir/identifier-system/endpoint",
                "value": "EP-1",
            }
        }
    ],
}

_PATCH_EXAMPLE = {
    "name": "Cardiology & Vascular Clinic",
    "telecom": [{"system": "phone", "value": "555-9999", "use": "work"}],
}


class HealthcareServiceCreateSchema(HealthcareService):
    "POST body - a FHIR R4 HealthcareService resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class HealthcareServicePatchSchema(HealthcareServicePatch):
    "PATCH body - a partial FHIR R4 HealthcareService (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

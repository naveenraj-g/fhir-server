"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.endpoint import Endpoint, EndpointPatch

_CREATE_EXAMPLE = {
    "resourceType": "Endpoint",
    "status": "active",
    "name": "General Hospital FHIR API",
    "managingOrganization": {
        "reference": "Organization/190001",
        "display": "General Hospital",
    },
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/endpoint",
            "value": "EP-1",
        }
    ],
    "connectionType": {
        "system": "http://terminology.hl7.org/CodeSystem/endpoint-connection-type",
        "code": "hl7-fhir-rest",
    },
    "payloadType": [{"coding": [{"code": "any", "display": "Any"}]}],
    "payloadMimeType": ["application/fhir+json"],
    "address": "https://fhir.generalhospital.example/r4",
    "header": ["Authorization: Bearer <token>"],
    "contact": [{"system": "email", "value": "it@generalhospital.example"}],
    "period": {"start": "2026-01-01T00:00:00Z"},
}

_PATCH_EXAMPLE = {
    "status": "suspended",
    "address": "https://fhir.generalhospital.example/r4-new",
}


class EndpointCreateSchema(Endpoint):
    "POST body - a FHIR R4 Endpoint resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class EndpointPatchSchema(EndpointPatch):
    "PATCH body - a partial FHIR R4 Endpoint (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

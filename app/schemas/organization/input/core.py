"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.organization import Organization, OrganizationPatch

_CREATE_EXAMPLE = {
    "resourceType": "Organization",
    "active": True,
    "name": "General Hospital",
    "partOf": {"reference": "Organization/190001", "display": "Parent Health System"},
    "identifier": [
        {
            "use": "official",
            "system": "https://fhir-server.dev/fhir/identifier-system/facility-id",
            "value": "12345",
            "assigner": {
                "reference": "Organization/190001",
                "display": "State Health Department",
            },
        }
    ],
    "type": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/organization-type",
                    "code": "prov",
                    "display": "Healthcare Provider",
                }
            ]
        }
    ],
    "alias": ["Gen Hosp"],
    "telecom": [{"system": "phone", "value": "555-1234", "use": "work"}],
    "address": [
        {
            "use": "work",
            "type": "both",
            "line": ["123 Main St"],
            "city": "Anytown",
            "state": "CA",
            "postalCode": "12345",
            "country": "US",
        }
    ],
    "contact": [
        {
            "purpose": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/contactentity-type",
                        "code": "ADMIN",
                    }
                ]
            },
            "name": {"family": "Smith", "given": ["John"]},
            "telecom": [{"system": "phone", "value": "555-0001"}],
            "address": {
                "type": "both",
                "city": "Anytown",
                "state": "CA",
                "country": "US",
            },
        }
    ],
    "endpoint": [
        {
            "display": "EHR FHIR Gateway",
            "identifier": {
                "system": "https://fhir-server.dev/fhir/identifier-system/endpoint",
                "value": "EP-1",
            },
        }
    ],
}

_PATCH_EXAMPLE = {
    "name": "General Hospital Health System",
    "alias": ["Gen Hosp", "GHHS"],
    "telecom": [{"system": "phone", "value": "555-9999", "use": "work"}],
}


class OrganizationCreateSchema(Organization):
    "POST body - a FHIR R4 Organization resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class OrganizationPatchSchema(OrganizationPatch):
    "PATCH body - a partial FHIR R4 Organization (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

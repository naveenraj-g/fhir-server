"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.organization import Organization, OrganizationPatch

_CREATE_EXAMPLE = {
    "resourceType": "Organization",
    "identifier": [
        {
            "use": "official",
            "system": "https://fhir-server.dev/fhir/identifier-system/facility-id",
            "value": "RGH-001",
        },
        {
            "use": "official",
            "system": "https://fhir-server.dev/fhir/identifier-system/gstin",
            "value": "29ABCDE1234F1Z5",
        },
        {
            "use": "official",
            "system": "https://fhir-server.dev/fhir/identifier-system/pan",
            "value": "ABCDE1234F",
        },
    ],
    "active": True,
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
    "name": "Riverside General Hospital",
    "alias": ["RGH"],
    "telecom": [
        {"system": "phone", "value": "+91-80-5550-0100", "use": "work"},
        {"system": "email", "value": "info@riverside-general.org", "use": "work"},
    ],
    "address": [
        {
            "use": "work",
            "type": "both",
            "line": ["12 Riverside Road", "Indiranagar"],
            "city": "Bengaluru",
            "state": "Karnataka",
            "postalCode": "560038",
            "country": "IN",
        }
    ],
    "contact": [
        {
            "purpose": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/contactentity-type",
                        "code": "ADMIN",
                        "display": "Administrative",
                    }
                ]
            },
            "name": {"use": "official", "family": "Carter", "given": ["Jordan"]},
            "telecom": [
                {"system": "phone", "value": "+91-80-5550-0110", "use": "work"}
            ],
        }
    ],
}

_PATCH_EXAMPLE = {
    "name": "General Hospital Health System",
    "alias": ["Gen Hosp", "GHHS"],
    "telecom": [{"system": "phone", "value": "+91-80-5550-9999", "use": "work"}],
}


class OrganizationCreateSchema(Organization):
    "POST body - a FHIR R4 Organization resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class OrganizationPatchSchema(OrganizationPatch):
    "PATCH body - a partial FHIR R4 Organization (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

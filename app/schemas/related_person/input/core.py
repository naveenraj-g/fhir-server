"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.related_person import RelatedPerson, RelatedPersonPatch

_CREATE_EXAMPLE = {
    "resourceType": "RelatedPerson",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/related-person-id",
            "value": "RP-1001",
        }
    ],
    "active": True,
    "patient": {"type": "Patient", "display": "Example patient"},
    "relationship": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                    "code": "MTH",
                    "display": "mother",
                }
            ]
        }
    ],
    "name": [{"use": "official", "family": "Windsor", "given": ["Mary"]}],
    "telecom": [{"system": "phone", "value": "555-9988", "use": "mobile"}],
    "gender": "female",
    "birthDate": "1965-04-12",
    "address": [
        {
            "use": "home",
            "line": ["1 Main St"],
            "city": "Boston",
            "state": "MA",
            "postalCode": "02110",
        }
    ],
    "communication": [{"language": {"coding": [{"code": "en"}]}, "preferred": True}],
}

_PATCH_EXAMPLE = {
    "active": False,
    "telecom": [{"system": "phone", "value": "555-0000"}],
}


class RelatedPersonCreateSchema(RelatedPerson):
    "POST body - a FHIR R4 RelatedPerson resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class RelatedPersonPatchSchema(RelatedPersonPatch):
    "PATCH body - a partial FHIR R4 RelatedPerson (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

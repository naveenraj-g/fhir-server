"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.practitioner import Practitioner, PractitionerPatch

_CREATE_EXAMPLE = {
    "resourceType": "Practitioner",
    "active": True,
    "gender": "female",
    "birthDate": "1980-05-15",
    "identifier": [
        {
            "use": "official",
            "system": "http://hl7.org/fhir/sid/us-npi",
            "value": "9941339108",
        }
    ],
    "name": [
        {"use": "official", "family": "Careful", "given": ["Adam"], "prefix": ["Dr"]}
    ],
    "telecom": [{"system": "phone", "value": "555-9988", "use": "work"}],
    "address": [
        {
            "use": "work",
            "line": ["534 Erewhon St"],
            "city": "PleasantVille",
            "state": "Vic",
            "postalCode": "3999",
        }
    ],
    "photo": [{"url": "https://fhir-server.dev/fhir/assets/photo.png"}],
    "qualification": [
        {
            "code": {
                "coding": [{"code": "BS", "display": "Bachelor of Science"}],
                "text": "Bachelor of Science",
            },
            "issuer": {"type": "Organization", "display": "Example organization"},
        }
    ],
    "communication": [{"coding": [{"code": "en", "display": "English"}]}],
}

_PATCH_EXAMPLE = {
    "telecom": [{"system": "phone", "value": "555-0000", "use": "work"}],
    "active": False,
}


class PractitionerCreateSchema(Practitioner):
    "POST body - a FHIR R4 Practitioner resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class PractitionerPatchSchema(PractitionerPatch):
    "PATCH body - a partial FHIR R4 Practitioner (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

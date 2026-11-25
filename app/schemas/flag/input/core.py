"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.flag import Flag, FlagPatch

_CREATE_EXAMPLE = {
    "resourceType": "Flag",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/flag-id",
            "value": "F-1",
        }
    ],
    "status": "active",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/flag-category",
                    "code": "safety",
                    "display": "Safety",
                }
            ]
        }
    ],
    "code": {"text": "Patient has a latex allergy"},
    "subject": {"reference": "Patient/10001"},
    "period": {"start": "2026-01-15"},
    "encounter": {"reference": "Encounter/20001"},
    "author": {"reference": "Practitioner/30001"},
}

_PATCH_EXAMPLE = {
    "status": "inactive",
    "period": {"start": "2026-01-15", "end": "2026-06-30"},
}


class FlagCreateSchema(Flag):
    "POST body - a FHIR R4 Flag resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class FlagPatchSchema(FlagPatch):
    "PATCH body - a partial FHIR R4 Flag (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.group import Group, GroupPatch

_CREATE_EXAMPLE = {
    "resourceType": "Group",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/group-id",
            "value": "GRP-1001",
        }
    ],
    "active": True,
    "type": "person",
    "actual": True,
    "code": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "385093006",
                "display": "Community",
            }
        ]
    },
    "name": "Diabetes cohort",
    "quantity": 2,
    "managingEntity": {"type": "Organization", "display": "Example organization"},
    "characteristic": [
        {
            "code": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "8302-2",
                        "display": "Body height",
                    }
                ]
            },
            "valueRange": {
                "low": {"value": 150, "unit": "cm"},
                "high": {"value": 190, "unit": "cm"},
            },
            "exclude": False,
        }
    ],
    "member": [
        {
            "entity": {"type": "Patient", "display": "Example patient"},
            "period": {"start": "2023-01-01"},
        },
        {
            "entity": {"type": "Patient", "display": "Example patient"},
            "inactive": False,
        },
    ],
}

_PATCH_EXAMPLE = {
    "active": False,
    "name": "Retired cohort",
    "member": [{"entity": {"type": "Patient", "display": "Example patient"}}],
}


class GroupCreateSchema(Group):
    "POST body - a FHIR R4 Group resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class GroupPatchSchema(GroupPatch):
    "PATCH body - a partial FHIR R4 Group (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

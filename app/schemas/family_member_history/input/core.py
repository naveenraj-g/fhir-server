"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.family_member_history import (
    FamilyMemberHistory,
    FamilyMemberHistoryPatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "FamilyMemberHistory",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/family-member-history-id",
            "value": "FMH-1001",
        }
    ],
    "status": "completed",
    "patient": {"type": "Patient", "display": "Example patient"},
    "date": "2023-01-15T09:30:00Z",
    "name": "Mary Windsor",
    "relationship": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                "code": "MTH",
                "display": "mother",
            }
        ]
    },
    "sex": {
        "coding": [
            {
                "system": "http://hl7.org/fhir/administrative-gender",
                "code": "female",
                "display": "Female",
            }
        ]
    },
    "bornDate": "1950-03-12",
    "deceasedBoolean": False,
    "reasonCode": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "160303001",
                    "display": "Family history of diabetes",
                }
            ]
        }
    ],
    "note": [{"text": "Mother has had type 2 diabetes since her forties."}],
    "condition": [
        {
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "44054006",
                        "display": "Type 2 diabetes mellitus",
                    }
                ]
            },
            "outcome": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "6736007",
                        "display": "Moderate",
                    }
                ]
            },
            "contributedToDeath": False,
            "onsetAge": {
                "value": 42,
                "unit": "yr",
                "system": "http://unitsofmeasure.org",
                "code": "a",
            },
        }
    ],
}

_PATCH_EXAMPLE = {
    "status": "entered-in-error",
    "note": [{"text": "Recorded against the wrong patient."}],
}


class FamilyMemberHistoryCreateSchema(FamilyMemberHistory):
    "POST body - a FHIR R4 FamilyMemberHistory resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class FamilyMemberHistoryPatchSchema(FamilyMemberHistoryPatch):
    "PATCH body - a partial FHIR R4 FamilyMemberHistory (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

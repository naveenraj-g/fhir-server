"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.procedure import Procedure, ProcedurePatch

_CREATE_EXAMPLE = {
    "resourceType": "Procedure",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/procedure-id",
            "value": "PR-1001",
        }
    ],
    "status": "completed",
    "category": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "387713003",
                "display": "Surgical procedure",
            }
        ]
    },
    "code": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "80146002",
                "display": "Appendectomy",
            }
        ]
    },
    "subject": {"type": "Patient", "display": "Example patient"},
    "encounter": {"type": "Encounter", "display": "Example encounter"},
    "performedPeriod": {"start": "2023-01-15T09:30:00Z", "end": "2023-01-15T10:45:00Z"},
    "recorder": {"type": "Practitioner", "display": "Example practitioner"},
    "asserter": {"type": "Practitioner", "display": "Example practitioner"},
    "performer": [
        {
            "function": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "304292004",
                        "display": "Surgeon",
                    }
                ]
            },
            "actor": {"type": "Practitioner", "display": "Example practitioner"},
        }
    ],
    "location": {"type": "Location", "display": "Example location"},
    "reasonCode": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "74400008",
                    "display": "Appendicitis",
                }
            ]
        }
    ],
    "bodySite": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "66754008",
                    "display": "Appendix",
                }
            ]
        }
    ],
    "outcome": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "385669000",
                "display": "Successful",
            }
        ]
    },
    "note": [{"text": "Uneventful.", "time": "2023-01-15T11:00:00Z"}],
}

_PATCH_EXAMPLE = {
    "status": "completed",
    "outcome": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "385669000",
                "display": "Successful",
            }
        ]
    },
}


class ProcedureCreateSchema(Procedure):
    "POST body - a FHIR R4 Procedure resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class ProcedurePatchSchema(ProcedurePatch):
    "PATCH body - a partial FHIR R4 Procedure (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

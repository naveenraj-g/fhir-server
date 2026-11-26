"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.immunization import Immunization, ImmunizationPatch

_CREATE_EXAMPLE = {
    "resourceType": "Immunization",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/immunization-id",
            "value": "IM-1001",
        }
    ],
    "status": "completed",
    "vaccineCode": {
        "coding": [
            {
                "system": "http://hl7.org/fhir/sid/cvx",
                "code": "140",
                "display": "Influenza, seasonal, injectable, preservative free",
            }
        ]
    },
    "patient": {"type": "Patient", "display": "Example patient"},
    "encounter": {"type": "Encounter", "display": "Example encounter"},
    "occurrenceDateTime": "2023-01-15T09:30:00Z",
    "recorded": "2023-01-15T10:00:00Z",
    "primarySource": True,
    "location": {"type": "Location", "display": "Example location"},
    "manufacturer": {"type": "Organization", "display": "Example organization"},
    "lotNumber": "AAJN11K",
    "expirationDate": "2025-02-15",
    "site": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActSite",
                "code": "LA",
                "display": "left arm",
            }
        ]
    },
    "route": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-RouteOfAdministration",
                "code": "IM",
                "display": "Injection, intramuscular",
            }
        ]
    },
    "doseQuantity": {"value": 5, "system": "http://unitsofmeasure.org", "code": "mg"},
    "performer": [
        {
            "function": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0443",
                        "code": "AP",
                    }
                ]
            },
            "actor": {"type": "Practitioner", "display": "Example practitioner"},
        }
    ],
    "note": [{"text": "Notes on adminstration of vaccine"}],
    "reasonCode": [
        {"coding": [{"system": "http://snomed.info/sct", "code": "429060002"}]}
    ],
    "isSubpotent": False,
    "protocolApplied": [
        {
            "series": "2-dose",
            "targetDisease": [
                {"coding": [{"system": "http://snomed.info/sct", "code": "40468003"}]}
            ],
            "doseNumberPositiveInt": 1,
        }
    ],
}

_PATCH_EXAMPLE = {
    "status": "entered-in-error",
    "note": [{"text": "Recorded against the wrong patient."}],
}


class ImmunizationCreateSchema(Immunization):
    "POST body - a FHIR R4 Immunization resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class ImmunizationPatchSchema(ImmunizationPatch):
    "PATCH body - a partial FHIR R4 Immunization (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

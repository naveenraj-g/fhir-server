"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.encounter import Encounter, EncounterPatch

_CREATE_EXAMPLE = {
    "resourceType": "Encounter",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/encounter-id",
            "value": "E-1001",
        }
    ],
    "status": "in-progress",
    "class": {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": "AMB",
        "display": "ambulatory",
    },
    "type": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "270427003",
                    "display": "Patient-initiated encounter",
                }
            ]
        }
    ],
    "priority": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActPriority",
                "code": "R",
            }
        ]
    },
    "subject": {"type": "Patient", "display": "Example patient"},
    "participant": [
        {
            "type": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                            "code": "ATND",
                        }
                    ]
                }
            ],
            "individual": {"type": "Practitioner", "display": "Example practitioner"},
        }
    ],
    "appointment": [{"type": "Appointment", "display": "Example appointment"}],
    "period": {"start": "2026-06-01T09:00:00Z"},
    "length": {
        "value": 1,
        "unit": "d",
        "system": "http://unitsofmeasure.org",
        "code": "d",
    },
    "reasonCode": [{"text": "Annual check-up"}],
    "location": [
        {
            "location": {"type": "Location", "display": "Example location"},
            "status": "active",
        }
    ],
    "serviceProvider": {"type": "Organization", "display": "Example organization"},
}

_PATCH_EXAMPLE = {
    "status": "finished",
    "period": {"start": "2026-06-01T09:00:00Z", "end": "2026-06-01T09:40:00Z"},
}


class EncounterCreateSchema(Encounter):
    "POST body - a FHIR R4 Encounter resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class EncounterPatchSchema(EncounterPatch):
    "PATCH body - a partial FHIR R4 Encounter (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

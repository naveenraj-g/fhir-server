"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.specimen import Specimen, SpecimenPatch

_CREATE_EXAMPLE = {
    "resourceType": "Specimen",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/specimen-id",
            "value": "SP-1001",
        }
    ],
    "accessionIdentifier": {
        "system": "http://lab.example.org/accessions",
        "value": "ACC-2023-0001",
    },
    "status": "available",
    "type": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v2-0487",
                "code": "BLD",
                "display": "Whole blood",
            }
        ]
    },
    "subject": {"reference": "Patient/10001"},
    "receivedTime": "2023-01-15T11:00:00Z",
    "collection": {
        "collector": {"reference": "Practitioner/30001"},
        "collectedDateTime": "2023-01-15T09:30:00Z",
        "quantity": {
            "value": 6,
            "unit": "mL",
            "system": "http://unitsofmeasure.org",
            "code": "mL",
        },
        "bodySite": {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "368208006",
                    "display": "Left upper arm structure",
                }
            ]
        },
    },
    "container": [
        {
            "identifier": [{"system": "urn:containers", "value": "C-1"}],
            "type": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "434746001",
                        "display": "Specimen vial",
                    }
                ]
            },
            "capacity": {
                "value": 10,
                "unit": "mL",
                "system": "http://unitsofmeasure.org",
                "code": "mL",
            },
        }
    ],
    "note": [{"text": "Fasting sample."}],
}

_PATCH_EXAMPLE = {"status": "unsatisfactory", "condition": [{"text": "Hemolyzed"}]}


class SpecimenCreateSchema(Specimen):
    "POST body - a FHIR R4 Specimen resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class SpecimenPatchSchema(SpecimenPatch):
    "PATCH body - a partial FHIR R4 Specimen (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

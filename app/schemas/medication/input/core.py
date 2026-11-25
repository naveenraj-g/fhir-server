"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.medication import Medication, MedicationPatch

_CREATE_EXAMPLE = {
    "resourceType": "Medication",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/medication-id",
            "value": "MED-1001",
        }
    ],
    "code": {
        "coding": [
            {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "1049502",
                "display": "12 HR Oxycodone Hydrochloride 10 MG Extended Release "
                "Oral Tablet",
            }
        ]
    },
    "status": "active",
    "manufacturer": {"reference": "Organization/190001"},
    "form": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "385057009",
                "display": "Film-coated tablet",
            }
        ]
    },
    "amount": {
        "numerator": {"value": 30, "unit": "tablet"},
        "denominator": {"value": 1, "unit": "package"},
    },
    "ingredient": [
        {
            "itemCodeableConcept": {
                "coding": [
                    {
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": "7804",
                        "display": "Oxycodone",
                    }
                ]
            },
            "isActive": True,
            "strength": {
                "numerator": {"value": 10, "unit": "mg"},
                "denominator": {"value": 1, "unit": "tablet"},
            },
        }
    ],
    "batch": {"lotNumber": "LOT-2026-1", "expirationDate": "2027-06-30"},
}

_PATCH_EXAMPLE = {
    "status": "inactive",
    "batch": {"lotNumber": "LOT-2026-2", "expirationDate": "2027-12-31"},
}


class MedicationCreateSchema(Medication):
    "POST body - a FHIR R4 Medication resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class MedicationPatchSchema(MedicationPatch):
    "PATCH body - a partial FHIR R4 Medication (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.medication_knowledge import (
    MedicationKnowledge,
    MedicationKnowledgePatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "MedicationKnowledge",
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
    "doseForm": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "385057009",
                "display": "Film-coated tablet",
            }
        ]
    },
    "amount": {"value": 30, "unit": "tablet"},
    "synonym": ["Oxycodone ER 10 mg"],
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
    "medicineClassification": [
        {
            "type": {"text": "therapeutic"},
            "classification": [
                {"coding": [{"system": "http://www.whocc.no/atc", "code": "N02AA05"}]}
            ],
        }
    ],
    "monitoringProgram": [{"name": "Opioid-Safety"}],
    "cost": [
        {
            "type": {"text": "wholesale"},
            "source": "Wholesaler-A",
            "cost": {"value": 12.5, "currency": "USD"},
        }
    ],
}

_PATCH_EXAMPLE = {
    "status": "inactive",
    "synonym": ["Oxycodone ER 10 mg", "OxyContin 10 mg"],
}


class MedicationKnowledgeCreateSchema(MedicationKnowledge):
    "POST body - a FHIR R4 MedicationKnowledge resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class MedicationKnowledgePatchSchema(MedicationKnowledgePatch):
    "PATCH body - a partial FHIR R4 MedicationKnowledge (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

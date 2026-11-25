"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.medication_statement import (
    MedicationStatement,
    MedicationStatementPatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "MedicationStatement",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/medication-statement-id",
            "value": "MS-1001",
        }
    ],
    "status": "active",
    "category": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/medication-statement-category",
                "code": "community",
            }
        ]
    },
    "medicationCodeableConcept": {
        "coding": [
            {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "197361",
                "display": "Amlodipine 5 MG Oral Tablet",
            }
        ]
    },
    "subject": {"reference": "Patient/10001"},
    "context": {"reference": "Encounter/20001"},
    "effectiveDateTime": "2026-01-15T10:00:00Z",
    "dateAsserted": "2026-01-15T10:05:00Z",
    "informationSource": {"reference": "Practitioner/30001"},
    "reasonCode": [
        {"coding": [{"system": "http://snomed.info/sct", "code": "38341003"}]}
    ],
    "note": [{"text": "Patient reports taking it in the morning."}],
    "dosage": [
        {
            "text": "5 mg once daily",
            "route": {
                "coding": [{"system": "http://snomed.info/sct", "code": "26643006"}]
            },
            "doseAndRate": [
                {
                    "doseQuantity": {
                        "value": 5,
                        "unit": "mg",
                        "system": "http://unitsofmeasure.org",
                        "code": "mg",
                    }
                }
            ],
        }
    ],
}

_PATCH_EXAMPLE = {
    "status": "stopped",
    "effectivePeriod": {"start": "2026-01-15", "end": "2026-03-01"},
}


class MedicationStatementCreateSchema(MedicationStatement):
    "POST body - a FHIR R4 MedicationStatement resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class MedicationStatementPatchSchema(MedicationStatementPatch):
    "PATCH body - a partial FHIR R4 MedicationStatement (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

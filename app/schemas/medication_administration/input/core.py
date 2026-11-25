"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.medication_administration import (
    MedicationAdministration,
    MedicationAdministrationPatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "MedicationAdministration",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/medication-administration-id",
            "value": "MA-1001",
        }
    ],
    "status": "completed",
    "category": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/medication-admin-category",
                "code": "inpatient",
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
    "performer": [{"actor": {"reference": "Practitioner/30001"}}],
    "reasonCode": [
        {"coding": [{"system": "http://snomed.info/sct", "code": "38341003"}]}
    ],
    "request": {"reference": "MedicationRequest/90001"},
    "dosage": {
        "text": "5 mg orally",
        "route": {"coding": [{"system": "http://snomed.info/sct", "code": "26643006"}]},
        "dose": {
            "value": 5,
            "unit": "mg",
            "system": "http://unitsofmeasure.org",
            "code": "mg",
        },
    },
}

_PATCH_EXAMPLE = {"status": "stopped", "statusReason": [{"text": "Patient refused"}]}


class MedicationAdministrationCreateSchema(MedicationAdministration):
    "POST body - a FHIR R4 MedicationAdministration resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class MedicationAdministrationPatchSchema(MedicationAdministrationPatch):
    "PATCH body - a partial FHIR R4 MedicationAdministration (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

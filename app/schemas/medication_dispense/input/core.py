"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.medication_dispense import (
    MedicationDispense,
    MedicationDispensePatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "MedicationDispense",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/medication-dispense-id",
            "value": "MD-1001",
        }
    ],
    "status": "completed",
    "category": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/medicationdispense-category",
                "code": "outpatient",
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
    "subject": {"type": "Patient", "display": "Example patient"},
    "context": {"type": "Encounter", "display": "Example encounter"},
    "performer": [
        {"actor": {"type": "Practitioner", "display": "Example practitioner"}}
    ],
    "authorizingPrescription": [
        {"type": "MedicationRequest", "display": "Example medication request"}
    ],
    "type": {
        "coding": [
            {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "FF"}
        ]
    },
    "quantity": {"value": 30, "unit": "tablet"},
    "daysSupply": {
        "value": 30,
        "unit": "Day",
        "system": "http://unitsofmeasure.org",
        "code": "d",
    },
    "whenPrepared": "2026-01-15T09:00:00Z",
    "whenHandedOver": "2026-01-15T10:00:00Z",
    "destination": {"type": "Location", "display": "Example location"},
    "receiver": [{"type": "Patient", "display": "Example patient"}],
    "dosageInstruction": [{"text": "1 tablet daily"}],
}

_PATCH_EXAMPLE = {
    "status": "cancelled",
    "statusReasonCodeableConcept": {"text": "Patient did not collect"},
}


class MedicationDispenseCreateSchema(MedicationDispense):
    "POST body - a FHIR R4 MedicationDispense resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class MedicationDispensePatchSchema(MedicationDispensePatch):
    "PATCH body - a partial FHIR R4 MedicationDispense (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.medication_request import (
    MedicationRequest,
    MedicationRequestPatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "MedicationRequest",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/prescription-id",
            "value": "RX-1001",
        }
    ],
    "status": "active",
    "intent": "order",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/medicationrequest-category",
                    "code": "outpatient",
                    "display": "Outpatient",
                }
            ]
        }
    ],
    "priority": "routine",
    "medicationCodeableConcept": {
        "coding": [
            {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "1049502",
                "display": "12 HR Oxycodone Hydrochloride "
                "10 MG Extended Release Oral "
                "Tablet",
            }
        ]
    },
    "subject": {"type": "Patient", "display": "Example patient"},
    "encounter": {"type": "Encounter", "display": "Example encounter"},
    "authoredOn": "2023-01-15T09:30:00Z",
    "requester": {"type": "Practitioner", "display": "Example practitioner"},
    "reasonCode": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "22253000",
                    "display": "Pain",
                }
            ]
        }
    ],
    "note": [{"text": "Take with food."}],
    "dosageInstruction": [
        {
            "sequence": 1,
            "text": "1 tablet every 12 hours",
            "timing": {"repeat": {"frequency": 1, "period": 12, "periodUnit": "h"}},
            "route": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "26643006",
                        "display": "Oral route",
                    }
                ]
            },
            "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}],
        }
    ],
    "dispenseRequest": {
        "validityPeriod": {"start": "2023-01-15", "end": "2023-07-15"},
        "numberOfRepeatsAllowed": 1,
        "quantity": {"value": 60, "unit": "tablet"},
        "expectedSupplyDuration": {
            "value": 30,
            "unit": "days",
            "system": "http://unitsofmeasure.org",
            "code": "d",
        },
    },
    "substitution": {"allowedBoolean": True},
}

_PATCH_EXAMPLE = {
    "status": "completed",
    "priority": "urgent",
    "note": [{"text": "Dispensed."}],
}


class MedicationRequestCreateSchema(MedicationRequest):
    "POST body - a FHIR R4 MedicationRequest resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class MedicationRequestPatchSchema(MedicationRequestPatch):
    "PATCH body - a partial FHIR R4 MedicationRequest (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

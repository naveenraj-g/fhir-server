"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.clinical_impression import (
    ClinicalImpression,
    ClinicalImpressionPatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "ClinicalImpression",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/clinical-impression-id",
            "value": "CI-1001",
        }
    ],
    "status": "completed",
    "code": {"text": "Initial assessment"},
    "description": "Assessment of the patient's chest pain.",
    "subject": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "effectiveDateTime": "2023-01-15T09:30:00Z",
    "date": "2023-01-15T10:00:00Z",
    "assessor": {"reference": "Practitioner/30001"},
    "problem": [{"reference": "Condition/120001"}],
    "investigation": [
        {
            "code": {"text": "Initial examination"},
            "item": [{"reference": "DiagnosticReport/110001"}],
        }
    ],
    "summary": "Stable angina suspected; stress test arranged.",
    "finding": [
        {
            "itemCodeableConcept": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "194828000",
                        "display": "Angina",
                    }
                ]
            },
            "basis": "Exercise ECG and history.",
        }
    ],
    "prognosisCodeableConcept": [{"text": "Good"}],
    "note": [{"text": "Review in 2 weeks."}],
}

_PATCH_EXAMPLE = {
    "status": "completed",
    "summary": "Stable angina confirmed after stress test.",
}


class ClinicalImpressionCreateSchema(ClinicalImpression):
    "POST body - a FHIR R4 ClinicalImpression resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class ClinicalImpressionPatchSchema(ClinicalImpressionPatch):
    "PATCH body - a partial FHIR R4 ClinicalImpression (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.diagnostic_report import (
    DiagnosticReport,
    DiagnosticReportPatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "DiagnosticReport",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/report-id",
            "value": "DR-1001",
        }
    ],
    "basedOn": [{"reference": "ServiceRequest/80001"}],
    "status": "final",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                    "code": "LAB",
                    "display": "Laboratory",
                }
            ]
        }
    ],
    "code": {
        "coding": [
            {
                "system": "http://loinc.org",
                "code": "58410-2",
                "display": "CBC panel - Blood by Automated count",
            }
        ]
    },
    "subject": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "effectiveDateTime": "2023-01-15T09:30:00Z",
    "issued": "2023-01-15T12:00:00Z",
    "performer": [{"reference": "Practitioner/30001"}],
    "resultsInterpreter": [{"reference": "Practitioner/30001"}],
    "specimen": [{"reference": "Specimen/310001"}],
    "result": [{"reference": "Observation/160001"}],
    "conclusion": "Normal blood count.",
    "conclusionCode": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "17621005",
                    "display": "Normal",
                }
            ]
        }
    ],
}

_PATCH_EXAMPLE = {"status": "amended", "conclusion": "Corrected: borderline anaemia."}


class DiagnosticReportCreateSchema(DiagnosticReport):
    "POST body - a FHIR R4 DiagnosticReport resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class DiagnosticReportPatchSchema(DiagnosticReportPatch):
    "PATCH body - a partial FHIR R4 DiagnosticReport (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

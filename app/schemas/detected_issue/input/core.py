"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.detected_issue import DetectedIssue, DetectedIssuePatch

_CREATE_EXAMPLE = {
    "resourceType": "DetectedIssue",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/detected-issue-id",
            "value": "DI-1001",
        }
    ],
    "status": "final",
    "code": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                "code": "DUPTHPY",
                "display": "Duplicate therapy alert",
            }
        ]
    },
    "severity": "high",
    "patient": {"reference": "Patient/10001"},
    "identifiedDateTime": "2023-01-15T09:30:00Z",
    "author": {"reference": "Practitioner/30001"},
    "implicated": [{"reference": "Condition/120001"}],
    "evidence": [
        {
            "code": [{"text": "Two active statin prescriptions"}],
            "detail": [{"reference": "DiagnosticReport/110001"}],
        }
    ],
    "detail": "The patient is prescribed two drugs of the same class.",
    "reference": "http://example.org/protocols/duplicate-therapy",
    "mitigation": [
        {
            "action": {"text": "Stopped the older prescription"},
            "date": "2023-01-16T08:00:00Z",
            "author": {"reference": "Practitioner/30001"},
        }
    ],
}

_PATCH_EXAMPLE = {"status": "amended", "severity": "moderate"}


class DetectedIssueCreateSchema(DetectedIssue):
    "POST body - a FHIR R4 DetectedIssue resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class DetectedIssuePatchSchema(DetectedIssuePatch):
    "PATCH body - a partial FHIR R4 DetectedIssue (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

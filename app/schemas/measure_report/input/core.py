"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.measure_report import MeasureReport, MeasureReportPatch

_CREATE_EXAMPLE = {
    "resourceType": "MeasureReport",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/measure-report-id",
            "value": "MR-1001",
        }
    ],
    "status": "complete",
    "type": "summary",
    "measure": "https://fhir-server.dev/fhir/Measure/readmission",
    "subject": {"type": "Group", "display": "Example group"},
    "date": "2026-02-01T10:00:00Z",
    "reporter": {"type": "Organization", "display": "Example organization"},
    "period": {"start": "2026-01-01", "end": "2026-01-31"},
    "improvementNotation": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/measure-improvement-notation",
                "code": "increase",
            }
        ]
    },
    "group": [
        {
            "code": {"text": "overall"},
            "population": [
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                                "code": "initial-population",
                            }
                        ]
                    },
                    "count": 120,
                },
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                                "code": "numerator",
                            }
                        ]
                    },
                    "count": 18,
                },
            ],
            "measureScore": {"value": 0.15},
        }
    ],
}

_PATCH_EXAMPLE = {"status": "complete", "date": "2026-02-02T10:00:00Z"}


class MeasureReportCreateSchema(MeasureReport):
    "POST body - a FHIR R4 MeasureReport resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class MeasureReportPatchSchema(MeasureReportPatch):
    "PATCH body - a partial FHIR R4 MeasureReport (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.task import Task, TaskPatch

_CREATE_EXAMPLE = {
    "resourceType": "Task",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/task-id",
            "value": "T-1",
        }
    ],
    "status": "requested",
    "intent": "order",
    "priority": "routine",
    "code": {
        "coding": [
            {"system": "http://hl7.org/fhir/CodeSystem/task-code", "code": "fulfill"}
        ]
    },
    "description": "Collect a blood sample",
    "focus": {"reference": "ServiceRequest/80001"},
    "for": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "authoredOn": "2026-01-15T09:00:00Z",
    "requester": {"reference": "Practitioner/30001"},
    "owner": {"reference": "Practitioner/30001"},
    "restriction": {"repetitions": 1, "period": {"end": "2026-02-15T00:00:00Z"}},
    "input": [{"type": {"text": "sample type"}, "valueString": "venous blood"}],
}

_PATCH_EXAMPLE = {
    "status": "completed",
    "businessStatus": {"text": "Specimen collected"},
}


class TaskCreateSchema(Task):
    "POST body - a FHIR R4 Task resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class TaskPatchSchema(TaskPatch):
    "PATCH body - a partial FHIR R4 Task (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

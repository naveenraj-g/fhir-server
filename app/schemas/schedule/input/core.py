"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.schedule import Schedule, SchedulePatch

_CREATE_EXAMPLE = {
    "resourceType": "Schedule",
    "active": True,
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/schedule-id",
            "value": "S-1",
        }
    ],
    "serviceCategory": [{"coding": [{"code": "17", "display": "General Practice"}]}],
    "serviceType": [{"coding": [{"code": "124", "display": "General Practice"}]}],
    "specialty": [{"coding": [{"code": "394579002", "display": "Cardiology"}]}],
    "actor": [
        {"reference": "Practitioner/30001", "display": "Dr Adam Careful"},
        {"reference": "Location/230001", "display": "Consulting room 1"},
    ],
    "planningHorizon": {"start": "2026-01-01T00:00:00Z", "end": "2026-12-31T23:59:59Z"},
    "comment": "Weekday clinic",
}

_PATCH_EXAMPLE = {
    "active": False,
    "planningHorizon": {"start": "2026-01-01T00:00:00Z", "end": "2026-06-30T23:59:59Z"},
}


class ScheduleCreateSchema(Schedule):
    "POST body - a FHIR R4 Schedule resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class SchedulePatchSchema(SchedulePatch):
    "PATCH body - a partial FHIR R4 Schedule (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.appointment import Appointment, AppointmentPatch

_CREATE_EXAMPLE = {
    "resourceType": "Appointment",
    "status": "booked",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/appointment-id",
            "value": "AP-1001",
        }
    ],
    "serviceCategory": [{"coding": [{"code": "17", "display": "General Practice"}]}],
    "serviceType": [{"coding": [{"code": "124", "display": "General Practice"}]}],
    "specialty": [{"coding": [{"code": "394579002", "display": "Cardiology"}]}],
    "appointmentType": {
        "coding": [{"code": "ROUTINE", "display": "Routine appointment"}]
    },
    "reasonCode": [{"text": "Annual check-up"}],
    "priority": 5,
    "description": "Discussion on the results of your recent MRI",
    "start": "2026-06-01T09:00:00Z",
    "end": "2026-06-01T09:30:00Z",
    "minutesDuration": 30,
    "slot": [{"reference": "Slot/220001"}],
    "created": "2026-05-20T10:00:00Z",
    "comment": "Further expand on the results of the MRI",
    "patientInstruction": "Please arrive 15 minutes early",
    "participant": [
        {
            "actor": {"reference": "Patient/10001"},
            "required": "required",
            "status": "accepted",
        },
        {
            "actor": {"reference": "Practitioner/30001"},
            "required": "required",
            "status": "accepted",
        },
    ],
    "requestedPeriod": [{"start": "2026-06-01", "end": "2026-06-07"}],
}

_PATCH_EXAMPLE = {
    "status": "cancelled",
    "cancelationReason": {"text": "Patient unwell"},
}


class AppointmentCreateSchema(Appointment):
    "POST body - a FHIR R4 Appointment resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class AppointmentPatchSchema(AppointmentPatch):
    "PATCH body - a partial FHIR R4 Appointment (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

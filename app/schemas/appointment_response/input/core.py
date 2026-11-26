"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.appointment_response import (
    AppointmentResponse,
    AppointmentResponsePatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "AppointmentResponse",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/appointment-response-id",
            "value": "AR-1001",
        }
    ],
    "appointment": {"type": "Appointment", "display": "Example appointment"},
    "start": "2026-06-01T09:00:00Z",
    "end": "2026-06-01T09:30:00Z",
    "participantType": [{"coding": [{"code": "ATND", "display": "attender"}]}],
    "actor": {"type": "Patient", "display": "Example patient"},
    "participantStatus": "accepted",
    "comment": "See you there",
}

_PATCH_EXAMPLE = {"participantStatus": "declined", "comment": "Cannot attend"}


class AppointmentResponseCreateSchema(AppointmentResponse):
    "POST body - a FHIR R4 AppointmentResponse resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class AppointmentResponsePatchSchema(AppointmentResponsePatch):
    "PATCH body - a partial FHIR R4 AppointmentResponse (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

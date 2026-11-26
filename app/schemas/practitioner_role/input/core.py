"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.practitioner_role import (
    PractitionerRole,
    PractitionerRolePatch,
)

_CREATE_EXAMPLE = {
    "resourceType": "PractitionerRole",
    "active": True,
    "period": {"start": "2026-01-01T00:00:00Z"},
    "practitioner": {"type": "Practitioner", "display": "Dr Adam Careful"},
    "organization": {"type": "Organization", "display": "General Hospital"},
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/role-id",
            "value": "R-1",
        }
    ],
    "code": [{"coding": [{"code": "doctor", "display": "Doctor"}]}],
    "specialty": [{"coding": [{"code": "394579002", "display": "Cardiology"}]}],
    "location": [{"type": "Location", "display": "Example location"}],
    "healthcareService": [
        {"type": "HealthcareService", "display": "Example healthcare service"}
    ],
    "telecom": [{"system": "phone", "value": "555-0100", "use": "work"}],
    "availableTime": [
        {
            "daysOfWeek": ["mon", "tue"],
            "availableStartTime": "08:00:00",
            "availableEndTime": "17:00:00",
        }
    ],
    "notAvailable": [
        {"description": "Conference week", "during": {"start": "2026-09-01T00:00:00Z"}}
    ],
    "availabilityExceptions": "Not on public holidays",
    "endpoint": [{"type": "Endpoint", "display": "Example endpoint"}],
}

_PATCH_EXAMPLE = {
    "active": False,
    "period": {"start": "2026-01-01T00:00:00Z", "end": "2026-12-31T23:59:59Z"},
}


class PractitionerRoleCreateSchema(PractitionerRole):
    "POST body - a FHIR R4 PractitionerRole resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class PractitionerRolePatchSchema(PractitionerRolePatch):
    "PATCH body - a partial FHIR R4 PractitionerRole (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

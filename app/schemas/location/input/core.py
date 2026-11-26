"""Request schemas: the FHIR R4 resource as the caller sends it (generated; see
scripts/generate_fhir_resources.py). The models are in app/schemas/fhir_resources/.
"""

from __future__ import annotations

from pydantic import ConfigDict

from app.schemas.fhir_resources.location import Location, LocationPatch

_CREATE_EXAMPLE = {
    "resourceType": "Location",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/location-ids",
            "value": "B1-S.F2",
        }
    ],
    "status": "active",
    "operationalStatus": {
        "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
        "code": "U",
        "display": "Unoccupied",
    },
    "name": "South Wing, second floor",
    "alias": [
        "BU MC, SW, F2",
        "Burgers University Medical Center, South Wing, second floor",
    ],
    "description": "Second floor of the Old South Wing, formerly in use by Psychiatry",
    "mode": "instance",
    "type": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                    "code": "HOSP",
                    "display": "Hospital",
                }
            ]
        }
    ],
    "telecom": [{"system": "phone", "value": "2328", "use": "work"}],
    "address": {
        "use": "work",
        "line": ["Galapagosweg 91, Building A"],
        "city": "Den Burg",
        "postalCode": "9105 PZ",
        "country": "NLD",
    },
    "physicalType": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
                "code": "wi",
                "display": "Wing",
            }
        ]
    },
    "position": {"longitude": -83.6945691, "latitude": 42.25475478, "altitude": 0},
    "managingOrganization": {"type": "Organization", "display": "Example organization"},
    "partOf": {"type": "Location", "display": "Burgers University Medical Center"},
    "hoursOfOperation": [
        {
            "daysOfWeek": ["mon", "tue", "wed", "thu", "fri"],
            "allDay": False,
            "openingTime": "09:00:00",
            "closingTime": "17:30:00",
        }
    ],
    "availabilityExceptions": "Reduced services on public holidays",
    "endpoint": [{"type": "Endpoint", "display": "Example endpoint"}],
}

_PATCH_EXAMPLE = {
    "status": "suspended",
    "operationalStatus": {
        "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
        "code": "K",
        "display": "Contaminated",
    },
}


class LocationCreateSchema(Location):
    "POST body - a FHIR R4 Location resource. The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body. The example can be sent as it is: where it points at another record it gives only `type` and `display`. Add `reference` (`Type/<id>`) to link a record that exists; it is checked on write."

    model_config = ConfigDict(json_schema_extra={"example": _CREATE_EXAMPLE})


class LocationPatchSchema(LocationPatch):
    "PATCH body - a partial FHIR R4 Location (merge-patch on top-level elements). Only supplied elements are written; a supplied element replaces the stored value wholesale (a list, even [], replaces every entry; null clears it). The body is validated as sent against base FHIR R4 and stored whole, so any valid R4 element is kept, including ones nothing searches on. `id` and `meta` are server-managed and ignored if sent. The organization and the audit fields come from the verified token, never the body."

    model_config = ConfigDict(json_schema_extra={"example": _PATCH_EXAMPLE})

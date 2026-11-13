"""Shared helpers and payloads for Location integration tests.

Request bodies are genuine FHIR R4 Location JSON (camelCase, nested
datatypes), and every response is FHIR R4 too — same as Organization."""

BASE = "/api/fhir/v1/locations"
ORG_BASE = "/api/fhir/v1/organizations"

MINIMAL = {"status": "active", "name": "Main Building", "mode": "instance"}

FULL = {
    "resourceType": "Location",
    "status": "active",
    "name": "South Wing, second floor",
    "mode": "instance",
    "description": "Second floor of the Old South Wing",
    "operationalStatus": {
        "system": "http://terminology.hl7.org/CodeSystem/v2-0116",
        "code": "U",
        "display": "Unoccupied",
    },
    "alias": ["South Wing OR"],
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/location-ids",
            "value": "B1-S.F2",
            "use": "official",
        }
    ],
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
        "type": "both",
        "line": ["Galapagosweg 91", "Building A"],
        "city": "Springfield",
        "state": "IL",
        "postalCode": "62701",
        "country": "US",
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
    "hoursOfOperation": [
        {
            "daysOfWeek": ["mon", "tue", "wed", "thu", "fri"],
            "allDay": False,
            "openingTime": "09:00:00",
            "closingTime": "17:30:00",
        }
    ],
    "availabilityExceptions": "Reduced services on public holidays",
    "endpoint": [{"identifier": {"system": "urn:ext-endpoint", "value": "EP-1"}}],
}


async def create_location(client, payload=None) -> int:
    """Create a location and return its public id (int)."""
    resp = await client.post(BASE + "/", json=payload or MINIMAL)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def create_organization(client, name: str = "Managing Org") -> int:
    resp = await client.post(ORG_BASE + "/", json={"active": True, "name": name})
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])

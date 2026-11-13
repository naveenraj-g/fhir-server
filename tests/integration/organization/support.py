"""Shared helpers and payloads for organization integration tests.

Request bodies are genuine FHIR R4 Organization JSON (camelCase, nested
datatypes), and every response is FHIR R4 too."""

BASE = "/api/fhir/v1/organizations"

MINIMAL = {
    "active": True,
    "name": "Test Hospital",
}

FULL = {
    "resourceType": "Organization",
    "active": True,
    "name": "General Hospital",
    "identifier": [
        {
            "system": "http://hl7.org/fhir/sid/us-npi",
            "value": "1234567893",
            "assigner": {
                "identifier": {
                    "system": "urn:external-registry",
                    "value": "EXTERNAL-1",
                }
            },
        }
    ],
    "type": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/organization-type",
                    "code": "prov",
                    "display": "Healthcare Provider",
                }
            ]
        }
    ],
    "alias": ["Gen Hosp"],
    "telecom": [{"system": "phone", "value": "555-1234", "use": "work"}],
    "address": [
        {
            "use": "work",
            "type": "both",
            "line": ["123 Main St"],
            "city": "Anytown",
            "state": "CA",
            "postalCode": "12345",
            "country": "US",
        }
    ],
    "contact": [
        {
            "purpose": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/contactentity-type",
                        "code": "ADMIN",
                    }
                ]
            },
            "name": {"family": "Smith", "given": ["John"]},
            "address": {
                "type": "both",
                "city": "Anytown",
                "state": "CA",
                "postalCode": "12345",
                "country": "US",
            },
            "telecom": [{"system": "phone", "value": "555-0001"}],
        }
    ],
    "endpoint": [
        {
            "identifier": {
                "system": "urn:ext-endpoint",
                "value": "EP-1",
            }
        }
    ],
}


async def create_organization(client, payload=None) -> int:
    """Create an organization and return the public organization id (int)."""
    payload = payload or MINIMAL
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])

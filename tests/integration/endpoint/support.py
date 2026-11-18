"""Shared helpers and payloads for endpoint integration tests.

Request bodies are genuine FHIR R4 Endpoint JSON (camelCase, nested
datatypes), and every response is FHIR R4 too."""

BASE = "/api/fhir/v1/endpoints"
ORG_BASE = "/api/fhir/v1/organizations"

CONN = "http://terminology.hl7.org/CodeSystem/endpoint-connection-type"
PAYLOAD = "http://terminology.hl7.org/CodeSystem/endpoint-payload-type"
EP_IDS = "https://fhir-server.dev/fhir/identifier-system/endpoint"

# R4 requires status, connectionType, payloadType and address.
MINIMAL = {
    "status": "active",
    "connectionType": {"system": CONN, "code": "hl7-fhir-rest"},
    "payloadType": [{"coding": [{"system": PAYLOAD, "code": "any"}]}],
    "address": "https://fhir.example.org/r4",
}

FULL = {
    "resourceType": "Endpoint",
    "status": "active",
    "name": "General Hospital FHIR API",
    "identifier": [
        {
            "system": EP_IDS,
            "value": "EP-1",
            "assigner": {"identifier": {"system": "urn:external-registry", "value": "EXTERNAL-1"}},
        }
    ],
    "connectionType": {"system": CONN, "code": "hl7-fhir-rest", "display": "HL7 FHIR"},
    "contact": [{"system": "email", "value": "it@example.org", "use": "work"}],
    "period": {"start": "2026-01-01T00:00:00Z", "end": "2027-01-01T00:00:00Z"},
    "payloadType": [{"coding": [{"system": PAYLOAD, "code": "any", "display": "Any"}], "text": "Any payload"}],
    "payloadMimeType": ["application/fhir+json", "application/fhir+xml"],
    "address": "https://fhir.example.org/r4",
    "header": ["Authorization: Bearer abc"],
}


async def create_endpoint(client, payload=None) -> int:
    """Create an endpoint and return its public id (int)."""
    resp = await client.post(BASE + "/", json=payload or MINIMAL)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def create_organization(client, name: str = "Managing Org") -> int:
    resp = await client.post(ORG_BASE + "/", json={"active": True, "name": name})
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])

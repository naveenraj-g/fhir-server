"""Shared helpers and payloads for organization integration tests."""

BASE = "/api/fhir/v1/organizations"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}

MINIMAL = {
    "user_id": "u-test",
    "active": True,
    "name": "Test Hospital",
}

FULL = {
    "user_id": "u-test",
    "active": True,
    "name": "General Hospital",
    "identifier": [
        {
            "system": "http://hl7.org/fhir/sid/us-npi",
            "value": "1234567893",
            "assigner_identifier_system": "urn:external-registry",
            "assigner_identifier_value": "EXTERNAL-1",
        }
    ],
    "type": [
        {
            "coding_system": "http://terminology.hl7.org/CodeSystem/organization-type",
            "coding_code": "prov",
            "coding_display": "Healthcare Provider",
        }
    ],
    "alias": [{"value": "Gen Hosp"}],
    "telecom": [{"system": "phone", "value": "555-1234", "use": "work"}],
    "address": [
        {
            "use": "work",
            "type": "both",
            "line": ["123 Main St"],
            "city": "Anytown",
            "state": "CA",
            "postal_code": "12345",
            "country": "US",
        }
    ],
    "contact": [
        {
            "purpose_code": "ADMIN",
            "purpose_system": "http://terminology.hl7.org/CodeSystem/contactentity-type",
            "name_family": "Smith",
            "name_given": ["John"],
            "address_type": "both",
            "address_city": "Anytown",
            "address_state": "CA",
            "address_postal_code": "12345",
            "address_country": "US",
            "telecom": [{"system": "phone", "value": "555-0001"}],
        }
    ],
    "endpoint": [
        {
            "reference_identifier_system": "urn:ext-endpoint",
            "reference_identifier_value": "EP-1",
        }
    ],
}


async def create_organization(client, payload=None) -> int:
    """Create an organization and return the public organization id."""
    payload = payload or MINIMAL
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]

"""Shared helpers and payloads for practitioner_role integration tests.

Request bodies are genuine FHIR R4 PractitionerRole JSON (camelCase, nested
datatypes), and every response is FHIR R4 too."""

BASE = "/api/fhir/v1/practitioner-roles"
API = "/api/fhir/v1"

ROLE_CS = "http://terminology.hl7.org/CodeSystem/practitioner-role"
SCT = "http://snomed.info/sct"
ROLE_IDS = "https://fhir-server.dev/fhir/identifier-system/role-id"

MINIMAL = {"active": True}

FULL = {
    "resourceType": "PractitionerRole",
    "active": True,
    "period": {"start": "2026-01-01T00:00:00Z", "end": "2026-12-31T23:59:59Z"},
    "identifier": [
        {
            "system": ROLE_IDS,
            "value": "R-1001",
            "assigner": {"identifier": {"system": "urn:external-registry", "value": "EXTERNAL-1"}},
        }
    ],
    "code": [{"coding": [{"system": ROLE_CS, "code": "doctor", "display": "Doctor"}]}],
    "specialty": [{"coding": [{"system": SCT, "code": "394579002", "display": "Cardiology"}]}],
    "telecom": [{"system": "phone", "value": "555-0100", "use": "work"}],
    "availableTime": [
        {"daysOfWeek": ["mon", "tue"], "availableStartTime": "08:00:00", "availableEndTime": "17:00:00"},
        {"daysOfWeek": ["sat"], "allDay": True},
    ],
    "notAvailable": [
        {"description": "Conference week", "during": {"start": "2026-09-01T00:00:00Z", "end": "2026-09-08T00:00:00Z"}}
    ],
    "availabilityExceptions": "Not on public holidays",
}


async def _create(client, path, body) -> int:
    resp = await client.post(f"{API}/{path}/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def create_role(client, payload=None) -> int:
    """Create a practitioner role and return its public id (int)."""
    return await _create(client, "practitioner-roles", payload or MINIMAL)


async def create_practitioner(client, family="Careful", given="Adam") -> int:
    return await _create(client, "practitioners", {"active": True, "name": [{"family": family, "given": [given]}]})


async def create_organization(client, name="Providing Org") -> int:
    return await _create(client, "organizations", {"active": True, "name": name})


async def create_location(client, name="North Wing", city="Boston") -> int:
    return await _create(
        client, "locations", {"status": "active", "name": name, "mode": "instance", "address": {"city": city}}
    )


async def create_healthcare_service(client, name="Cardiology Clinic") -> int:
    return await _create(client, "healthcare-services", {"active": True, "name": name})


async def create_endpoint(client, name="Role API") -> int:
    return await _create(
        client,
        "endpoints",
        {
            "status": "active",
            "name": name,
            "connectionType": {"code": "hl7-fhir-rest"},
            "payloadType": [{"text": "any"}],
            "address": "https://fhir.example.org/r4",
        },
    )

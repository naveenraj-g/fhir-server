"""Shared helpers and payloads for schedule integration tests.

Request bodies are genuine FHIR R4 Schedule JSON (camelCase, nested
datatypes), and every response is FHIR R4 too."""

# The resources an actor can point at are created through their own routers.
from tests.integration.practitioner_role.support import (  # noqa: F401
    create_healthcare_service,
    create_location,
    create_organization,
    create_practitioner,
    create_role as create_practitioner_role,
)

BASE = "/api/fhir/v1/schedules"

SCHED_IDS = "https://fhir-server.dev/fhir/identifier-system/schedule-id"
CAT = "http://terminology.hl7.org/CodeSystem/service-category"
TYPE = "http://terminology.hl7.org/CodeSystem/service-type"
SCT = "http://snomed.info/sct"

# R4 requires at least one actor. The default one is a Patient on another system (an absolute URL
# is not existence-checked), so a schedule can be created without creating a patient first.
EXTERNAL_PATIENT = "https://other.example.org/fhir/Patient/77"
MINIMAL = {"active": True, "actor": [{"reference": EXTERNAL_PATIENT}]}

FULL = {
    "resourceType": "Schedule",
    "active": True,
    "identifier": [
        {
            "system": SCHED_IDS,
            "value": "S-1001",
            "assigner": {
                "identifier": {"system": "urn:external-registry", "value": "EXTERNAL-1"}
            },
        }
    ],
    "serviceCategory": [
        {
            "coding": [{"system": CAT, "code": "17", "display": "General Practice"}],
            "text": "General",
        }
    ],
    "serviceType": [
        {"coding": [{"system": TYPE, "code": "124", "display": "General Practice"}]}
    ],
    "specialty": [
        {"coding": [{"system": SCT, "code": "394579002", "display": "Cardiology"}]}
    ],
    "actor": [
        {"reference": EXTERNAL_PATIENT, "display": "A patient"},
        {"reference": "Device/5"},
    ],
    "planningHorizon": {"start": "2026-01-01T00:00:00Z", "end": "2026-12-31T23:59:59Z"},
    "comment": "Weekday clinic",
}


async def create_schedule(client, payload=None) -> int:
    """Create a schedule and return its public id (int)."""
    resp = await client.post(BASE + "/", json=payload or MINIMAL)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])

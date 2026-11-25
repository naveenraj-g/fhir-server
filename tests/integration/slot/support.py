"""Shared helpers and payloads for slot integration tests.

Request bodies are genuine FHIR R4 Slot JSON (camelCase, nested datatypes),
and every response is FHIR R4 too."""

from tests.integration.schedule.support import (
    create_organization,
    create_practitioner,
    create_schedule,
)

BASE = "/api/fhir/v1/slots"

SLOT_IDS = "https://fhir-server.dev/fhir/identifier-system/slot-id"
CAT = "http://terminology.hl7.org/CodeSystem/service-category"
TYPE = "http://terminology.hl7.org/CodeSystem/service-type"
APPT = "http://terminology.hl7.org/CodeSystem/v2-0276"
SCT = "http://snomed.info/sct"

START = "2026-06-01T09:00:00Z"
END = "2026-06-01T09:30:00Z"


def slot_body(schedule_id: int, **changes) -> dict:
    """A valid minimal Slot for a schedule: R4 requires schedule, status,
    start and end."""
    return {
        "schedule": {"reference": f"Schedule/{schedule_id}"},
        "status": "free",
        "start": START,
        "end": END,
        **changes,
    }


def full_body(schedule_id: int) -> dict:
    return slot_body(
        schedule_id,
        resourceType="Slot",
        identifier=[
            {
                "system": SLOT_IDS,
                "value": "SL-1001",
                "assigner": {
                    "identifier": {
                        "system": "urn:external-registry",
                        "value": "EXTERNAL-1",
                    }
                },
            }
        ],
        serviceCategory=[
            {
                "coding": [
                    {"system": CAT, "code": "17", "display": "General Practice"}
                ],
                "text": "General",
            }
        ],
        serviceType=[
            {"coding": [{"system": TYPE, "code": "124", "display": "General Practice"}]}
        ],
        specialty=[
            {"coding": [{"system": SCT, "code": "394579002", "display": "Cardiology"}]}
        ],
        appointmentType={
            "coding": [
                {"system": APPT, "code": "ROUTINE", "display": "Routine appointment"}
            ],
            "text": "Routine",
        },
        overbooked=False,
        comment="Bring previous reports",
    )


async def create_slot(client, body: dict) -> int:
    """Create a slot and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])

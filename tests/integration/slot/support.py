"""Shared helpers and payloads for slot integration tests.

Slot.schedule is a required (1..1), existence-validated reference — unlike
Schedule's mocked-via-identifier-fallback actors, every test here needs a
real Schedule row, seeded through the now-mounted /schedules endpoint (see
configs/config.yaml's routes.enabled)."""

BASE = "/api/fhir/v1/slots"
SCHEDULE_BASE = "/api/fhir/v1/schedules"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}

SCHEDULE_MINIMAL = {
    "active": True,
    "actor": [
        {
            "reference_identifier_system": "urn:actor-registry",
            "reference_identifier_value": "ACTOR-1",
        }
    ],
}


async def create_schedule(client, payload=None) -> int:
    """Create a Schedule — a real dependency for Slot.schedule, not a mock —
    and return its public schedule_id."""
    payload = payload if payload is not None else SCHEDULE_MINIMAL
    resp = await client.post(SCHEDULE_BASE + "/", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


def minimal_slot_payload(schedule_id: int, **overrides) -> dict:
    payload = {
        "schedule": f"Schedule/{schedule_id}",
        "status": "free",
        "start": "2024-06-01T09:00:00Z",
        "end": "2024-06-01T09:30:00Z",
    }
    payload.update(overrides)
    return payload


def full_slot_payload(schedule_id: int, **overrides) -> dict:
    payload = {
        "schedule": f"Schedule/{schedule_id}",
        "schedule_display": "Dr. Smith's schedule",
        "status": "free",
        "start": "2024-06-01T09:00:00Z",
        "end": "2024-06-01T09:30:00Z",
        "overbooked": False,
        "comment": "Morning slot — first appointment of the day",
        "appointment_type_system": "http://terminology.hl7.org/CodeSystem/v2-0276",
        "appointment_type_code": "ROUTINE",
        "appointment_type_display": "Routine appointment",
        "identifier": [
            {
                "system": "http://example.org/slot-ids",
                "value": "SLOT-1001",
                "assigner_identifier_system": "urn:external-registry",
                "assigner_identifier_value": "EXTERNAL-1",
            }
        ],
        "service_category": [
            {
                "coding_system": "http://example.org/service-category",
                "coding_code": "17",
                "coding_display": "General Practice",
            }
        ],
        "service_type": [{"coding_code": "57", "coding_display": "Immunization"}],
        "specialty": [
            {
                "coding_system": "http://snomed.info/sct",
                "coding_code": "394814009",
                "coding_display": "General practice",
            }
        ],
    }
    payload.update(overrides)
    return payload


async def create_slot(client, schedule_id: int | None = None, payload=None) -> int:
    """Create a slot and return its public slot_id. Seeds a real Schedule
    first (unless schedule_id/payload is supplied) since Slot.schedule is a
    required, existence-validated reference."""
    if payload is None:
        if schedule_id is None:
            schedule_id = await create_schedule(client)
        payload = minimal_slot_payload(schedule_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]

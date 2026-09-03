"""Shared helpers and payloads for schedule integration tests."""

import datetime as dt

from app.models.practitioner import PractitionerModel
from app.schemas.enums import AdministrativeGender

BASE = "/api/fhir/v1/schedules"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}

MINIMAL = {
    "active": True,
    "actor": [
        {
            "reference_identifier_system": "urn:actor-registry",
            "reference_identifier_value": "ACTOR-1",
        }
    ],
}

FULL = {
    "active": True,
    "comment": "Available for urgent bookings only.",
    "planning_horizon_start": "2024-01-01T08:00:00Z",
    "planning_horizon_end": "2024-12-31T12:00:00Z",
    "identifier": [
        {
            "system": "http://example.org/sched-ids",
            "value": "SCHED-1001",
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
    "service_type": [
        {"coding_code": "57", "coding_display": "Immunization"}
    ],
    "specialty": [
        {
            "coding_system": "http://snomed.info/sct",
            "coding_code": "394814009",
            "coding_display": "General practice",
        }
    ],
    "actor": [
        {
            "reference_identifier_system": "urn:actor-registry",
            "reference_identifier_value": "ACTOR-9",
        }
    ],
}


async def create_schedule(client, payload=None) -> int:
    """Create a schedule and return the public schedule id."""
    payload = payload or MINIMAL
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


async def seed_practitioner(
    engine, *, practitioner_id: int = 30001, org_id: str = "org-test"
) -> int:
    """Insert a minimal Practitioner row directly (Practitioner's own router
    isn't mounted in this test env — see configs/config.yaml's routes.enabled)
    so Schedule's `actor` resolved-reference existence check
    (`_validate_actor_reference`) has a real row to resolve."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_maker() as session:
        session.add(
            PractitionerModel(
                practitioner_id=practitioner_id,
                org_id=org_id,
                active=True,
                gender=AdministrativeGender.male,
                birth_date=dt.date(1980, 1, 1),
                created_by="u-test",
                created_at=dt.datetime.now(dt.timezone.utc),
            )
        )
        await session.commit()
    return practitioner_id

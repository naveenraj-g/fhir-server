"""Shared helpers and payloads for practitioner_role integration tests."""

import datetime as dt

from app.models.location import LocationMode, LocationModel, LocationStatus
from app.models.practitioner import PractitionerModel
from app.schemas.enums import AdministrativeGender

BASE = "/api/fhir/v1/practitioner-roles"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}

MINIMAL = {
    "active": True,
}

FULL = {
    "active": True,
    "period_start": "2024-01-01T00:00:00Z",
    "availability_exceptions": "Not available on public holidays",
    "identifier": [
        {
            "system": "http://example.org/pr-ids",
            "value": "PR-1001",
            "assigner_identifier_system": "urn:external-registry",
            "assigner_identifier_value": "EXTERNAL-1",
        }
    ],
    "code": [
        {
            "coding_system": "http://snomed.info/sct",
            "coding_code": "59058001",
            "coding_display": "General physician",
        }
    ],
    "specialty": [
        {
            "coding_system": "http://snomed.info/sct",
            "coding_code": "394814009",
            "coding_display": "General practice",
        }
    ],
    "location": [
        {
            "reference_identifier_system": "urn:loc-registry",
            "reference_identifier_value": "LOC-9",
        }
    ],
    "healthcare_service": [
        {
            "reference_identifier_system": "urn:hs-registry",
            "reference_identifier_value": "HS-9",
        }
    ],
    "telecom": [{"system": "phone", "value": "555-1234", "use": "work"}],
    "available_time": [
        {
            "days_of_week": ["mon", "tue", "wed", "thu", "fri"],
            "available_start_time": "09:00:00",
            "available_end_time": "17:00:00",
        }
    ],
    "not_available": [
        {
            "description": "Annual leave.",
            "during_start": "2026-06-01T00:00:00Z",
            "during_end": "2026-06-07T00:00:00Z",
        }
    ],
    "endpoint": [
        {
            "reference_identifier_system": "urn:ext-endpoint",
            "reference_identifier_value": "EP-1",
        }
    ],
}


async def create_practitioner_role(client, payload=None) -> int:
    """Create a practitioner role and return the public practitioner_role id."""
    payload = payload or MINIMAL
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


async def seed_location(
    engine, *, location_id: int = 230001, org_id: str = "org-test"
) -> int:
    """Insert a minimal Location row directly (Location's own router isn't
    mounted in this test env — see configs/config.yaml's routes.enabled) so
    PractitionerRole's `location` resolved-reference existence check
    (`_validate_reference`) has a real row to resolve."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_maker() as session:
        session.add(
            LocationModel(
                location_id=location_id,
                org_id=org_id,
                status=LocationStatus.active,
                name="Test Location",
                mode=LocationMode.instance,
                address_type="both",
                address_city="Test City",
                address_state="TS",
                address_postal_code="00000",
                address_country="USA",
                created_by="u-test",
                created_at=dt.datetime.now(dt.timezone.utc),
            )
        )
        await session.commit()
    return location_id


async def seed_practitioner(
    engine, *, practitioner_id: int = 30001, org_id: str = "org-test"
) -> int:
    """Insert a minimal Practitioner row directly (Practitioner's own router
    isn't mounted in this test env either) so PractitionerRole's
    `practitioner` resolved-reference existence check has a real row."""
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

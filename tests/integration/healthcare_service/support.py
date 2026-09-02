"""Shared helpers and payloads for healthcare_service integration tests."""

import datetime as dt

from app.models.location import LocationMode, LocationModel, LocationStatus

BASE = "/api/fhir/v1/healthcare-services"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}

MINIMAL = {
    "active": True,
    "name": "Test Healthcare Service",
}

FULL = {
    "active": True,
    "name": "Cardiology Services",
    "comment": "Specializing in cardiac care",
    "extra_details": "Extended hours on Tuesdays.",
    "appointment_required": True,
    "availability_exceptions": "Closed public holidays",
    "identifier": [
        {
            "system": "http://example.org/hs-ids",
            "value": "HS-1001",
            "assigner_identifier_system": "urn:external-registry",
            "assigner_identifier_value": "EXTERNAL-1",
        }
    ],
    "category": [
        {
            "coding_system": "http://terminology.hl7.org/CodeSystem/service-category",
            "coding_code": "8",
            "coding_display": "Counselling",
        }
    ],
    "type": [
        {
            "coding_system": "http://snomed.info/sct",
            "coding_code": "394579002",
            "coding_display": "Cardiology",
        }
    ],
    "specialty": [
        {
            "coding_system": "http://snomed.info/sct",
            "coding_code": "394579002",
            "coding_display": "Cardiology",
        }
    ],
    "telecom": [{"system": "phone", "value": "555-1234", "use": "work"}],
    "location": [
        {
            "reference_identifier_system": "urn:loc-registry",
            "reference_identifier_value": "LOC-9",
        }
    ],
    "coverage_area": [
        {
            "reference_identifier_system": "urn:loc-registry",
            "reference_identifier_value": "LOC-8",
        }
    ],
    "service_provision_code": [
        {
            "coding_system": "http://terminology.hl7.org/CodeSystem/service-provision-conditions",
            "coding_code": "free",
            "coding_display": "Free",
        }
    ],
    "eligibility": [
        {
            "code_code": "ind",
            "code_display": "Indigenous population",
            "comment": "Must provide proof of eligibility.",
        }
    ],
    "program": [
        {
            "coding_system": "http://example.org/programs",
            "coding_code": "mh",
            "coding_display": "Mental Health",
        }
    ],
    "characteristic": [
        {
            "coding_system": "http://example.org/characteristics",
            "coding_code": "wheelchair",
            "coding_display": "Wheelchair accessible",
        }
    ],
    "communication": [
        {"coding_system": "urn:ietf:bcp:47", "coding_code": "en", "coding_display": "English"}
    ],
    "referral_method": [
        {
            "coding_system": "http://example.org/referral-method",
            "coding_code": "phone",
            "coding_display": "Phone",
        }
    ],
    "available_time": [
        {
            "days_of_week": ["mon", "tue", "wed", "thu", "fri"],
            "available_start_time": "09:00:00",
            "available_end_time": "17:00:00",
        }
    ],
    "not_available": [
        {
            "description": "Closed for renovations.",
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


async def create_healthcare_service(client, payload=None) -> int:
    """Create a healthcare service and return the public healthcare_service id."""
    payload = payload or MINIMAL
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()["id"]


async def seed_location(
    engine, *, location_id: int = 230001, org_id: str = "org-test"
) -> int:
    """Insert a minimal Location row directly (Location's own router isn't
    mounted in this test env — see configs/config.yaml's routes.enabled) so
    HealthcareService's `location`/`coverageArea` resolved-reference
    existence check (`_validate_reference`) has a real row to resolve."""
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

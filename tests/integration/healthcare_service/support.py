"""Shared helpers and payloads for healthcare_service integration tests.

Request bodies are genuine FHIR R4 HealthcareService JSON (camelCase, nested
datatypes), and every response is FHIR R4 too."""

import datetime as dt

from app.models.location import LocationModel, LocationStatus

BASE = "/api/fhir/v1/healthcare-services"
ORG_BASE = "/api/fhir/v1/organizations"

MINIMAL = {"active": True, "name": "Test Healthcare Service"}

# Systems here are deliberately made-up https://fhir-server.dev/... URLs and
# codings carry no `system` where a real one would make the Java validator
# sidecar attempt a slow remote terminology lookup.
SERVICE_ID_SYSTEM = "https://fhir-server.dev/fhir/identifier-system/hs-ids"

FULL = {
    "resourceType": "HealthcareService",
    "active": True,
    "name": "Cardiology Services",
    "comment": "Specializing in cardiac care",
    "extraDetails": "Extended hours on Tuesdays.",
    "appointmentRequired": True,
    "availabilityExceptions": "Closed public holidays",
    "identifier": [
        {
            "system": SERVICE_ID_SYSTEM,
            "value": "HS-1001",
            "assigner": {
                "identifier": {"system": "urn:external-registry", "value": "EXTERNAL-1"}
            },
        }
    ],
    "category": [
        {
            "coding": [{"code": "35", "display": "Specialist Medical"}],
            "text": "Specialist",
        }
    ],
    "type": [{"coding": [{"code": "124", "display": "General Practice"}]}],
    "specialty": [{"coding": [{"code": "394579002", "display": "Cardiology"}]}],
    "telecom": [{"system": "phone", "value": "555-0100", "use": "work"}],
    "serviceProvisionCode": [{"coding": [{"code": "free", "display": "Free"}]}],
    "eligibility": [{"code": {"text": "Over 18"}, "comment": "Adults only"}],
    "program": [{"coding": [{"code": "diabetes", "display": "Diabetes"}]}],
    "characteristic": [
        {"coding": [{"code": "wheelchair", "display": "Wheelchair access"}]}
    ],
    "communication": [{"coding": [{"code": "en", "display": "English"}]}],
    "referralMethod": [{"coding": [{"code": "phone", "display": "Phone"}]}],
    "availableTime": [
        {
            "daysOfWeek": ["mon", "tue"],
            "availableStartTime": "08:00:00",
            "availableEndTime": "17:00:00",
        },
        {"daysOfWeek": ["sat"], "allDay": True},
    ],
    "notAvailable": [
        {
            "description": "Closed for the holidays",
            "during": {"start": "2026-12-24T00:00:00Z", "end": "2026-12-26T00:00:00Z"},
        }
    ],
    "endpoint": [{"identifier": {"system": "urn:ext-endpoint", "value": "EP-1"}}],
}


async def create_healthcare_service(client, payload=None) -> int:
    """Create a healthcare service and return its public id (int)."""
    resp = await client.post(BASE + "/", json=payload or MINIMAL)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def create_organization(client, name: str = "Providing Org") -> int:
    resp = await client.post(ORG_BASE + "/", json={"active": True, "name": name})
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


async def seed_location(
    engine,
    *,
    location_id: int = 230001,
    org_id: str = "org-test",
    name: str = "Test Location",
    city: str = "Test City",
) -> int:
    """Insert a minimal Location row directly (Location's own router isn't
    mounted in this test env — see configs/config.yaml's routes.enabled) so
    HealthcareService's `location`/`coverageArea` resolved-reference
    existence check has a real row to resolve, and `_include` / chaining have
    something to return."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_maker() as session:
        session.add(
            LocationModel(
                location_id=location_id,
                tenant_id=org_id,
                content={
                    "status": "active",
                    "name": name,
                    "mode": "instance",
                    "address": {
                        "city": city,
                        "state": "TS",
                        "postalCode": "00000",
                        "country": "USA",
                    },
                },
                # Search-index columns for the fields above (normally derived
                # by app.repository.location._indexer).
                status=LocationStatus.active,
                name=name,
                name_norm=name.casefold(),
                address_city=city,
                address_city_norm=city.casefold(),
                created_by="u-test",
                created_at=dt.datetime.now(dt.timezone.utc),
            )
        )
        await session.commit()
    return location_id

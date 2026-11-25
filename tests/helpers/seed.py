"""Direct DB seeding for tests that need a row from another resource without
going through its router (and its permissions)."""

import datetime as dt

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.models.endpoint import EndpointModel, EndpointStatus


async def seed_endpoint(
    engine,
    *,
    endpoint_id: int = 620001,
    org_id: str = "org-test",
    name: str = "Seeded Endpoint",
    managing_organization_id: int | None = None,
) -> int:
    """Insert a minimal Endpoint row so a `Reference(Endpoint)` from an
    Organization / Location / HealthcareService has a real row to resolve.
    Its search-index columns are set directly (normally derived by
    app.repository.endpoint._indexer)."""
    session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with session_maker() as session:
        session.add(
            EndpointModel(
                endpoint_id=endpoint_id,
                tenant_id=org_id,
                created_by="u-test",
                created_at=dt.datetime.now(dt.UTC),
                content={
                    "status": "active",
                    "connectionType": {"code": "hl7-fhir-rest"},
                    "name": name,
                    "payloadType": [{"text": "any"}],
                    "address": "https://fhir.example.org/r4",
                },
                status=EndpointStatus.active,
                connection_type_code="hl7-fhir-rest",
                name=name,
                name_norm=name.casefold(),
                managing_organization_id=managing_organization_id,
            )
        )
        await session.commit()
    return endpoint_id

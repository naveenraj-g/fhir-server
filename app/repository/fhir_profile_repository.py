from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.fhir_profile.enums import FhirProfileScopeLevel
from app.models.fhir_profile.fhir_profile import FhirProfile


class FhirProfileRepository:
    """All DB I/O for fhir_profile — plain reads only, no write path exists
    yet for any of the three scope levels (base is seeded once, never
    admin-editable; country has no admin write path yet either — see
    app/fhir/profiling/README.md and app/fhir_profile/seed_*.py;
    organization has no seeding or write path at all yet)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def get_base(self, resource_type: str) -> FhirProfile | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(FhirProfile)
                .where(FhirProfile.resource_type == resource_type)
                .where(FhirProfile.scope_level == FhirProfileScopeLevel.base)
                .order_by(FhirProfile.id.desc())
            )
            return result.scalars().first()

    async def get_country(
        self, resource_type: str, country_code: str
    ) -> FhirProfile | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(FhirProfile)
                .where(FhirProfile.resource_type == resource_type)
                .where(FhirProfile.scope_level == FhirProfileScopeLevel.country)
                .where(FhirProfile.scope_id == country_code)
                .order_by(FhirProfile.id.desc())
            )
            return result.scalars().first()

    async def get_organization(
        self, resource_type: str, org_id: str
    ) -> FhirProfile | None:
        """scope_id here is the owning organization's public org_id (see
        FhirProfile's own docstring), not a country code — same column,
        different meaning depending on scope_level."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(FhirProfile)
                .where(FhirProfile.resource_type == resource_type)
                .where(FhirProfile.scope_level == FhirProfileScopeLevel.organization)
                .where(FhirProfile.scope_id == org_id)
                .order_by(FhirProfile.id.desc())
            )
            return result.scalars().first()

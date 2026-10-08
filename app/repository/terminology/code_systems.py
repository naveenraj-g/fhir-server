from sqlalchemy import select

from app.models.terminology.terminology import TerminologyCodeSystem


class _CodeSystemsMixin:
    async def list_code_systems(self) -> list[TerminologyCodeSystem]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(TerminologyCodeSystem)
                .where(TerminologyCodeSystem.active == True)
                .order_by(TerminologyCodeSystem.name)
            )
            return list(result.scalars().all())

    async def get_code_system_by_url(self, url: str) -> TerminologyCodeSystem | None:
        async with self.session_factory() as session:
            row = await session.execute(
                select(TerminologyCodeSystem).where(
                    TerminologyCodeSystem.canonical_url == url
                )
            )
            return row.scalar_one_or_none()

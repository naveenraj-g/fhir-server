from sqlalchemy import select

from app.models.practitioner import PractitionerModel, PractitionerTelecom
from app.schemas.practitioner import PractitionerTelecomCreate, PractitionerTelecomPatch

from ._shared import _delete_child, _fetch_child


class _TelecomMixin:
    """Full lifecycle (add/list/delete/patch) for Practitioner.telecom rows."""

    async def add_telecom(
        self, practitioner_id: int, payload: PractitionerTelecomCreate, created_by: str | None = None,
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            row = PractitionerTelecom(
                practitioner_id=practitioner.id,
                org_id=practitioner.org_id,
                system=payload.system,
                value=payload.value,
                use=payload.use,
                rank=payload.rank,
                period_start=payload.period_start,
                period_end=payload.period_end,
                created_by=created_by,
            )
            try:
                session.add(row)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_practitioner_id(practitioner_id)

    async def get_telecoms(self, practitioner_id: int) -> list:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return []
            return list((await session.execute(
                select(PractitionerTelecom).where(PractitionerTelecom.practitioner_id == practitioner.id)
            )).scalars().all())

    async def delete_telecom(self, practitioner_id: int, telecom_id: int) -> bool:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return False
            return await _delete_child(session, PractitionerTelecom, telecom_id, practitioner.id)

    async def patch_telecom(
        self, practitioner_id: int, telecom_id: int, payload: PractitionerTelecomPatch,
        updated_by: str | None = None,
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return None
            row = await _fetch_child(session, PractitionerTelecom, telecom_id, practitioner.id)
            if not row:
                return None
            for field, value in payload.model_dump(exclude_unset=True).items():
                setattr(row, field, value)
            if updated_by is not None:
                row.updated_by = updated_by
            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_practitioner_id(practitioner_id)

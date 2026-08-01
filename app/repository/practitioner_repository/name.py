from sqlalchemy import select

from app.models.practitioner import PractitionerModel, PractitionerName
from app.schemas.practitioner import PractitionerNameCreate, PractitionerNamePatch

from ._shared import _delete_child, _fetch_child


class _NameMixin:
    """Full lifecycle (add/list/delete/patch) for Practitioner.name rows."""

    async def add_name(
        self, practitioner_id: int, payload: PractitionerNameCreate, created_by: str | None = None,
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            row = PractitionerName(
                practitioner_id=practitioner.id,
                org_id=practitioner.org_id,
                use=payload.use,
                text=payload.text,
                family=payload.family,
                given=",".join(payload.given) if payload.given else None,
                prefix=",".join(payload.prefix) if payload.prefix else None,
                suffix=",".join(payload.suffix) if payload.suffix else None,
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

    async def get_names(self, practitioner_id: int) -> list:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return []
            return list((await session.execute(
                select(PractitionerName).where(PractitionerName.practitioner_id == practitioner.id)
            )).scalars().all())

    async def delete_name(self, practitioner_id: int, name_id: int) -> bool:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return False
            return await _delete_child(session, PractitionerName, name_id, practitioner.id)

    async def patch_name(
        self, practitioner_id: int, name_id: int, payload: PractitionerNamePatch, updated_by: str | None = None,
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return None
            row = await _fetch_child(session, PractitionerName, name_id, practitioner.id)
            if not row:
                return None
            data = payload.model_dump(exclude_unset=True)
            for field in ("given", "prefix", "suffix"):
                if field in data:
                    data[field] = ",".join(data[field]) if data[field] else None
            for field, value in data.items():
                setattr(row, field, value)
            if updated_by is not None:
                row.updated_by = updated_by
            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_practitioner_id(practitioner_id)

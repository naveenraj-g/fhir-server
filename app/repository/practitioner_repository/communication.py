from sqlalchemy import select

from app.models.practitioner import PractitionerCommunication, PractitionerModel
from app.schemas.practitioner import PractitionerCommunicationCreate, PractitionerCommunicationPatch

from ._shared import _delete_child, _fetch_child


class _CommunicationMixin:
    """Full lifecycle (add/list/delete/patch) for Practitioner.communication rows."""

    async def add_communication(
        self, practitioner_id: int, payload: PractitionerCommunicationCreate, created_by: str | None = None,
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            row = PractitionerCommunication(
                practitioner_id=practitioner.id,
                org_id=practitioner.org_id,
                language_system=payload.language_system,
                language_version=payload.language_version,
                language_code=payload.language_code,
                language_display=payload.language_display,
                language_text=payload.language_text,
                language_user_selected=payload.language_user_selected,
                created_by=created_by,
            )
            try:
                session.add(row)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_practitioner_id(practitioner_id)

    async def get_communications(self, practitioner_id: int) -> list:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return []
            return list((await session.execute(
                select(PractitionerCommunication).where(PractitionerCommunication.practitioner_id == practitioner.id)
            )).scalars().all())

    async def delete_communication(self, practitioner_id: int, comm_id: int) -> bool:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return False
            return await _delete_child(session, PractitionerCommunication, comm_id, practitioner.id)

    async def patch_communication(
        self, practitioner_id: int, comm_id: int, payload: PractitionerCommunicationPatch,
        updated_by: str | None = None,
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return None
            row = await _fetch_child(session, PractitionerCommunication, comm_id, practitioner.id)
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

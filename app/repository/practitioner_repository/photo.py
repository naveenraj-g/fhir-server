from sqlalchemy import select

from app.models.practitioner import PractitionerModel, PractitionerPhoto
from app.schemas.practitioner import PractitionerPhotoCreate, PractitionerPhotoPatch

from ._shared import _delete_child, _fetch_child


class _PhotoMixin:
    """Full lifecycle (add/list/delete/patch) for Practitioner.photo rows."""

    async def add_photo(
        self, practitioner_id: int, payload: PractitionerPhotoCreate, created_by: str | None = None,
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            stmt = select(PractitionerModel).where(PractitionerModel.practitioner_id == practitioner_id)
            practitioner = (await session.execute(stmt)).scalars().first()
            if not practitioner:
                return None
            row = PractitionerPhoto(
                practitioner_id=practitioner.id,
                org_id=practitioner.org_id,
                content_type=payload.content_type,
                language=payload.language,
                data=payload.data,
                url=payload.url,
                size=payload.size,
                hash=payload.hash,
                title=payload.title,
                creation=payload.creation,
                created_by=created_by,
            )
            try:
                session.add(row)
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_practitioner_id(practitioner_id)

    async def get_photos(self, practitioner_id: int) -> list:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return []
            return list((await session.execute(
                select(PractitionerPhoto).where(PractitionerPhoto.practitioner_id == practitioner.id)
            )).scalars().all())

    async def delete_photo(self, practitioner_id: int, photo_id: int) -> bool:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return False
            return await _delete_child(session, PractitionerPhoto, photo_id, practitioner.id)

    async def patch_photo(
        self, practitioner_id: int, photo_id: int, payload: PractitionerPhotoPatch,
        updated_by: str | None = None,
    ) -> PractitionerModel | None:
        async with self.session_factory() as session:
            practitioner = await self._get_internal(session, practitioner_id)
            if not practitioner:
                return None
            row = await _fetch_child(session, PractitionerPhoto, photo_id, practitioner.id)
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

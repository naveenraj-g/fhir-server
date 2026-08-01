from sqlalchemy import select

from app.models.patient.patient import PatientModel, PatientPhoto
from app.schemas.patient import PhotoCreate, PhotoPatch

from ._shared import _delete_child, _fetch_child


class _PhotoMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.photo rows."""

    async def add_photo(
        self, patient_id: int, payload: PhotoCreate, created_by: str | None = None
    ) -> PatientModel | None:
        """Append one photo attachment row to this patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            photo = PatientPhoto(
                patient_id=patient.id,
                org_id=patient.org_id,
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
                session.add(photo)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def get_photos(self, patient_id: int) -> list:
        """All photo attachment rows for this patient. Backs GET /{patient_id}/photos."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return []
            result = await session.execute(
                select(PatientPhoto).where(PatientPhoto.patient_id == patient.id)
            )
            return list(result.scalars().all())

    async def delete_photo(self, patient_id: int, photo_id: int) -> bool:
        """Delete one photo attachment row — False if it doesn't exist or belongs to a different patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return False
            return await _delete_child(session, PatientPhoto, photo_id, patient.id)

    async def patch_photo(
        self,
        patient_id: int,
        photo_id: int,
        payload: PhotoPatch,
        updated_by: str | None = None,
    ) -> PatientModel | None:
        """Partial update of one photo attachment row via generic setattr from model_dump(exclude_unset=True)."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None
            row = await _fetch_child(session, PatientPhoto, photo_id, patient.id)
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
        return await self.get_by_patient_id(patient_id)

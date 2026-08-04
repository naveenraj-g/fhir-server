from sqlalchemy import select

from app.models.patient import PatientLink, PatientModel
from app.schemas.patient import LinkCreate, LinkPatch

from ._shared import _delete_child, _fetch_child, _reference_kwargs, _validate_reference


class _LinkMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.link rows."""

    async def add_link(
        self, patient_id: int, payload: LinkCreate, created_by: str | None = None
    ) -> PatientModel | None:
        """Append one patient-link row to this patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            await _validate_reference(
                session, patient.org_id, payload.other_type, payload.other_id, "link.other"
            )
            link = PatientLink(
                patient_id=patient.id,
                org_id=patient.org_id,
                other_type=payload.other_type,
                other_id=payload.other_id,
                other_display=payload.other_display,
                **_reference_kwargs("other", payload),
                type=payload.type,
                created_by=created_by,
            )
            try:
                session.add(link)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def get_links(self, patient_id: int) -> list:
        """All patient-link rows for this patient. Backs GET /{patient_id}/links."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return []
            result = await session.execute(
                select(PatientLink).where(PatientLink.patient_id == patient.id)
            )
            return list(result.scalars().all())

    async def delete_link(self, patient_id: int, link_id: int) -> bool:
        """Delete one patient-link row — False if it doesn't exist or belongs to a different patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return False
            return await _delete_child(session, PatientLink, link_id, patient.id)

    async def patch_link(
        self,
        patient_id: int,
        link_id: int,
        payload: LinkPatch,
        updated_by: str | None = None,
    ) -> PatientModel | None:
        """Partial update of one patient-link row via generic setattr from model_dump(exclude_unset=True)."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None
            row = await _fetch_child(session, PatientLink, link_id, patient.id)
            if not row:
                return None
            data = payload.model_dump(exclude_unset=True)
            for field, value in data.items():
                setattr(row, field, value)
            if "other_type" in data or "other_id" in data:
                await _validate_reference(
                    session, patient.org_id, row.other_type, row.other_id, "link.other"
                )
            if updated_by is not None:
                row.updated_by = updated_by
            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_patient_id(patient_id)

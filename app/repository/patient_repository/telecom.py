from sqlalchemy import select

from app.models.patient.patient import PatientModel, PatientTelecom
from app.schemas.patient import TelecomCreate, TelecomPatch

from ._shared import _delete_child, _fetch_child


class _TelecomMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.telecom rows."""

    async def add_telecom(
        self, patient_id: int, payload: TelecomCreate, created_by: str | None = None
    ) -> PatientModel | None:
        """Append one contact-point row to this patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            telecom = PatientTelecom(
                patient_id=patient.id,
                org_id=patient.org_id,
                system=payload.system,
                value=payload.value,
                use=payload.use,
                rank=payload.rank,
                period_start=payload.period_start,
                period_end=payload.period_end,
                created_by=created_by,
            )
            try:
                session.add(telecom)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def get_telecoms(self, patient_id: int) -> list:
        """All contact-point rows for this patient. Backs GET /{patient_id}/telecom."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return []
            result = await session.execute(
                select(PatientTelecom).where(PatientTelecom.patient_id == patient.id)
            )
            return list(result.scalars().all())

    async def delete_telecom(self, patient_id: int, telecom_id: int) -> bool:
        """Delete one contact-point row — False if it doesn't exist or belongs to a different patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return False
            return await _delete_child(
                session, PatientTelecom, telecom_id, patient.id
            )

    async def patch_telecom(
        self,
        patient_id: int,
        telecom_id: int,
        payload: TelecomPatch,
        updated_by: str | None = None,
    ) -> PatientModel | None:
        """Partial update of one contact-point row via generic setattr from model_dump(exclude_unset=True)."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None
            row = await _fetch_child(
                session, PatientTelecom, telecom_id, patient.id
            )
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

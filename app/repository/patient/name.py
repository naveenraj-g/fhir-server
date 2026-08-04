from sqlalchemy import select

from app.models.patient import PatientModel, PatientName
from app.schemas.patient import NameCreate, NamePatch

from ._shared import _delete_child, _fetch_child


class _NameMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.name rows."""

    async def add_name(
        self, patient_id: int, payload: NameCreate, created_by: str | None = None
    ) -> PatientModel | None:
        """Append one HumanName row to this patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            name = PatientName(
                patient_id=patient.id,
                org_id=patient.org_id,
                use=payload.use,
                text=payload.text,
                family=payload.family,
                given=", ".join(payload.given) if payload.given else None,
                prefix=", ".join(payload.prefix) if payload.prefix else None,
                suffix=", ".join(payload.suffix) if payload.suffix else None,
                period_start=payload.period_start,
                period_end=payload.period_end,
                created_by=created_by,
            )
            try:
                session.add(name)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def get_names(self, patient_id: int) -> list:
        """All HumanName rows for this patient. Backs GET /{patient_id}/names."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return []
            result = await session.execute(
                select(PatientName).where(PatientName.patient_id == patient.id)
            )
            return list(result.scalars().all())

    async def delete_name(self, patient_id: int, name_id: int) -> bool:
        """Delete one HumanName row — False if it doesn't exist or belongs to a different patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return False
            return await _delete_child(session, PatientName, name_id, patient.id)

    async def patch_name(
        self,
        patient_id: int,
        name_id: int,
        payload: NamePatch,
        updated_by: str | None = None,
    ) -> PatientModel | None:
        """Partial update of one HumanName row via generic setattr from model_dump(exclude_unset=True)."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None
            row = await _fetch_child(session, PatientName, name_id, patient.id)
            if not row:
                return None
            data = payload.model_dump(exclude_unset=True)
            for field in ("given", "prefix", "suffix"):
                if field in data:
                    data[field] = ", ".join(data[field]) if data[field] else None
            for field, value in data.items():
                setattr(row, field, value)
            if updated_by is not None:
                row.updated_by = updated_by
            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_patient_id(patient_id)

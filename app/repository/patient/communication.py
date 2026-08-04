from sqlalchemy import select

from app.models.patient import PatientCommunication, PatientModel
from app.schemas.patient import CommunicationCreate, CommunicationPatch

from ._shared import _delete_child, _fetch_child


class _CommunicationMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.communication rows."""

    async def add_communication(
        self,
        patient_id: int,
        payload: CommunicationCreate,
        created_by: str | None = None,
    ) -> PatientModel | None:
        """Append one communication-language row to this patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            comm = PatientCommunication(
                patient_id=patient.id,
                org_id=patient.org_id,
                language_system=payload.language_system,
                language_version=payload.language_version,
                language_code=payload.language_code,
                language_display=payload.language_display,
                language_text=payload.language_text,
                language_user_selected=payload.language_user_selected,
                preferred=payload.preferred,
                created_by=created_by,
            )
            try:
                session.add(comm)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def get_communications(self, patient_id: int) -> list:
        """All communication-language rows for this patient. Backs GET /{patient_id}/communications."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return []
            result = await session.execute(
                select(PatientCommunication).where(
                    PatientCommunication.patient_id == patient.id
                )
            )
            return list(result.scalars().all())

    async def delete_communication(self, patient_id: int, comm_id: int) -> bool:
        """Delete one communication-language row — False if it doesn't exist or belongs to a different patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return False
            return await _delete_child(
                session, PatientCommunication, comm_id, patient.id
            )

    async def patch_communication(
        self,
        patient_id: int,
        comm_id: int,
        payload: CommunicationPatch,
        updated_by: str | None = None,
    ) -> PatientModel | None:
        """Partial update of one communication-language row via generic setattr from model_dump(exclude_unset=True)."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None
            row = await _fetch_child(
                session, PatientCommunication, comm_id, patient.id
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

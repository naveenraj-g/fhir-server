from sqlalchemy import select

from app.models.patient.patient import PatientGeneralPractitioner, PatientModel
from app.schemas.patient import GeneralPractitionerCreate, GeneralPractitionerPatch

from ._shared import _delete_child, _fetch_child, _reference_kwargs, _validate_reference


class _GeneralPractitionerMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.generalPractitioner rows."""

    async def add_general_practitioner(
        self,
        patient_id: int,
        payload: GeneralPractitionerCreate,
        created_by: str | None = None,
    ) -> PatientModel | None:
        """Append one general-practitioner reference row to this patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            await _validate_reference(
                session,
                patient.org_id,
                payload.reference_type,
                payload.reference_id,
                "generalPractitioner",
            )
            gp = PatientGeneralPractitioner(
                patient_id=patient.id,
                org_id=patient.org_id,
                reference_type=payload.reference_type,
                reference_id=payload.reference_id,
                reference_display=payload.reference_display,
                **_reference_kwargs("reference", payload),
                created_by=created_by,
            )
            try:
                session.add(gp)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def get_general_practitioners(self, patient_id: int) -> list:
        """All general-practitioner reference rows for this patient. Backs GET /{patient_id}/general-practitioners."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return []
            result = await session.execute(
                select(PatientGeneralPractitioner).where(
                    PatientGeneralPractitioner.patient_id == patient.id
                )
            )
            return list(result.scalars().all())

    async def delete_general_practitioner(self, patient_id: int, gp_id: int) -> bool:
        """Delete one general-practitioner reference row — False if it doesn't exist or belongs to a different patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return False
            return await _delete_child(
                session, PatientGeneralPractitioner, gp_id, patient.id
            )

    async def patch_general_practitioner(
        self,
        patient_id: int,
        gp_id: int,
        payload: GeneralPractitionerPatch,
        updated_by: str | None = None,
    ) -> PatientModel | None:
        """Partial update of one general-practitioner reference row via generic setattr from model_dump(exclude_unset=True)."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None
            row = await _fetch_child(
                session, PatientGeneralPractitioner, gp_id, patient.id
            )
            if not row:
                return None
            data = payload.model_dump(exclude_unset=True)
            for field, value in data.items():
                setattr(row, field, value)
            if "reference_type" in data or "reference_id" in data:
                await _validate_reference(
                    session,
                    patient.org_id,
                    row.reference_type,
                    row.reference_id,
                    "generalPractitioner",
                )
            if updated_by is not None:
                row.updated_by = updated_by
            try:
                await session.commit()
            except Exception:
                await session.rollback()
                raise
        return await self.get_by_patient_id(patient_id)

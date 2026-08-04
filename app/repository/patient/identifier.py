from sqlalchemy import select

from app.models.patient import PatientIdentifier, PatientModel
from app.schemas.patient import IdentifierCreate, IdentifierPatch

from ._shared import _delete_child, _fetch_child, _org_ref_kwargs, _parse_org_ref, _reference_kwargs, _validate_reference


class _IdentifierMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.identifier rows."""

    async def add_identifier(
        self, patient_id: int, payload: IdentifierCreate, created_by: str | None = None
    ) -> PatientModel | None:
        """Append one business identifier row to this patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            a_type, a_id = (
                _parse_org_ref(payload.assigner) if payload.assigner else (None, None)
            )
            await _validate_reference(
                session, patient.org_id, a_type, a_id, "identifier.assigner"
            )
            ident = PatientIdentifier(
                patient_id=patient.id,
                org_id=patient.org_id,
                use=payload.use,
                type_system=payload.type_system,
                type_version=payload.type_version,
                type_code=payload.type_code,
                type_display=payload.type_display,
                type_text=payload.type_text,
                type_user_selected=payload.type_user_selected,
                system=payload.system,
                value=payload.value,
                period_start=payload.period_start,
                period_end=payload.period_end,
                **_org_ref_kwargs(
                    "assigner", payload.assigner, payload.assigner_display
                ),
                **_reference_kwargs("assigner", payload),
                created_by=created_by,
            )
            try:
                session.add(ident)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def get_identifiers(self, patient_id: int) -> list:
        """All identifier rows for this patient. Backs GET /{patient_id}/identifiers."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return []
            result = await session.execute(
                select(PatientIdentifier).where(
                    PatientIdentifier.patient_id == patient.id
                )
            )
            return list(result.scalars().all())

    async def delete_identifier(self, patient_id: int, identifier_id: int) -> bool:
        """Delete one identifier row — False if it doesn't exist or belongs to a different patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return False
            return await _delete_child(
                session, PatientIdentifier, identifier_id, patient.id
            )

    async def patch_identifier(
        self,
        patient_id: int,
        identifier_id: int,
        payload: IdentifierPatch,
        updated_by: str | None = None,
    ) -> PatientModel | None:
        """Partial update of one identifier row via generic setattr from model_dump(exclude_unset=True)."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None
            row = await _fetch_child(
                session, PatientIdentifier, identifier_id, patient.id
            )
            if not row:
                return None
            data = payload.model_dump(exclude_unset=True)
            if "assigner" in data:
                ref = data.pop("assigner")
                if ref:
                    a_type, a_id = _parse_org_ref(ref)
                    await _validate_reference(
                        session, patient.org_id, a_type, a_id, "identifier.assigner"
                    )
                    row.assigner_type = a_type
                    row.assigner_id = a_id
                else:
                    row.assigner_type = None
                    row.assigner_id = None
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

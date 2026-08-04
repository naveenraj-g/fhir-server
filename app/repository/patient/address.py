from sqlalchemy import select

from app.models.patient import PatientAddress, PatientModel
from app.schemas.patient import AddressCreate, AddressPatch

from ._shared import _delete_child, _fetch_child


class _AddressMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.address rows."""

    async def add_address(
        self, patient_id: int, payload: AddressCreate, created_by: str | None = None
    ) -> PatientModel | None:
        """Append one address row to this patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None

            address = PatientAddress(
                patient_id=patient.id,
                org_id=patient.org_id,
                use=payload.use,
                type=payload.type,
                text=payload.text,
                line=", ".join(payload.line) if payload.line else None,
                city=payload.city,
                district=payload.district,
                state=payload.state,
                postal_code=payload.postal_code,
                country=payload.country,
                period_start=payload.period_start,
                period_end=payload.period_end,
                created_by=created_by,
            )
            try:
                session.add(address)
                await session.commit()
            except Exception:
                await session.rollback()
                raise

        return await self.get_by_patient_id(patient_id)

    async def get_addresses(self, patient_id: int) -> list:
        """All address rows for this patient. Backs GET /{patient_id}/addresses."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return []
            result = await session.execute(
                select(PatientAddress).where(PatientAddress.patient_id == patient.id)
            )
            return list(result.scalars().all())

    async def delete_address(self, patient_id: int, address_id: int) -> bool:
        """Delete one address row — False if it doesn't exist or belongs to a different patient."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return False
            return await _delete_child(
                session, PatientAddress, address_id, patient.id
            )

    async def patch_address(
        self,
        patient_id: int,
        address_id: int,
        payload: AddressPatch,
        updated_by: str | None = None,
    ) -> PatientModel | None:
        """Partial update of one address row via generic setattr from model_dump(exclude_unset=True)."""
        async with self.session_factory() as session:
            patient = await self._get_internal(session, patient_id)
            if not patient:
                return None
            row = await _fetch_child(
                session, PatientAddress, address_id, patient.id
            )
            if not row:
                return None
            data = payload.model_dump(exclude_unset=True)
            if "line" in data:
                data["line"] = ", ".join(data["line"]) if data["line"] else None
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

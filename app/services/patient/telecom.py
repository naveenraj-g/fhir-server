from app.errors.domain import NotFoundError
from app.models.patient import PatientModel
from app.schemas.patient import TelecomCreate, TelecomPatch


class _TelecomMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.telecom rows.
    Every method validates the parent patient via get_patient_scoped() first."""

    async def add_telecom(
        self,
        patient_id: int,
        payload: TelecomCreate,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Append one contact-point row to this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.add_telecom(patient_id, payload, created_by)
        if not updated:
            raise NotFoundError("Patient not found")
        return updated

    async def get_telecoms(self, patient_id: int, org_id: str | None = None) -> list:
        """All contact-point rows for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_telecoms(patient_id)

    async def delete_telecom(
        self, patient_id: int, telecom_id: int, org_id: str | None = None
    ) -> None:
        """Delete one contact-point row."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_telecom(patient_id, telecom_id)
        if not deleted:
            raise NotFoundError("Telecom not found on this Patient")

    async def patch_telecom(
        self,
        patient_id: int,
        telecom_id: int,
        payload: TelecomPatch,
        org_id: str | None = None,
        updated_by: str | None = None,
    ) -> PatientModel:
        """Partial update of one contact-point row."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.patch_telecom(
            patient_id, telecom_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Telecom not found on this Patient")
        return updated

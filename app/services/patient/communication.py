from app.errors.domain import NotFoundError
from app.models.patient import PatientModel
from app.schemas.patient import CommunicationCreate, CommunicationPatch


class _CommunicationMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.communication rows.
    Every method validates the parent patient via get_patient_scoped() first."""

    async def add_communication(
        self,
        patient_id: int,
        payload: CommunicationCreate,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Append one communication-language row to this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.add_communication(
            patient_id, payload, created_by
        )
        if not updated:
            raise NotFoundError("Patient not found")
        return updated

    async def get_communications(
        self, patient_id: int, org_id: str | None = None
    ) -> list:
        """All communication-language rows for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_communications(patient_id)

    async def delete_communication(
        self, patient_id: int, comm_id: int, org_id: str | None = None
    ) -> None:
        """Delete one communication-language row."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_communication(patient_id, comm_id)
        if not deleted:
            raise NotFoundError("Communication not found on this Patient")

    async def patch_communication(
        self,
        patient_id: int,
        comm_id: int,
        payload: CommunicationPatch,
        org_id: str | None = None,
        updated_by: str | None = None,
    ) -> PatientModel:
        """Partial update of one communication-language row."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.patch_communication(
            patient_id, comm_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Communication not found on this Patient")
        return updated

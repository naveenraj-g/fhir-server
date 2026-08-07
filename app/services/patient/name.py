from app.core.logging import get_logger
from app.errors.domain import NotFoundError
from app.models.patient import PatientModel
from app.schemas.patient import NameCreate, NamePatch


logger = get_logger(__name__)


class _NameMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.name rows. Every
    method validates the parent patient via get_patient_scoped() first."""

    async def add_name(
        self,
        patient_id: int,
        payload: NameCreate,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Append one HumanName row to this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.add_name(patient_id, payload, created_by)
        if not updated:
            raise NotFoundError("Patient not found")
        logger.info(
            "Patient name added",
            extra={"event": "patient.name.added", "patient_id": patient_id},
        )
        return updated

    async def get_names(self, patient_id: int, org_id: str | None = None) -> list:
        """All HumanName rows for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_names(patient_id)

    async def delete_name(
        self, patient_id: int, name_id: int, org_id: str | None = None
    ) -> None:
        """Delete one HumanName row."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_name(patient_id, name_id)
        if not deleted:
            raise NotFoundError("Name not found on this Patient")
        logger.info(
            "Patient name deleted",
            extra={"event": "patient.name.deleted", "patient_id": patient_id, "name_id": name_id},
        )

    async def patch_name(
        self,
        patient_id: int,
        name_id: int,
        payload: NamePatch,
        org_id: str | None = None,
        updated_by: str | None = None,
    ) -> PatientModel:
        """Partial update of one HumanName row."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.patch_name(
            patient_id, name_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Name not found on this Patient")
        logger.info(
            "Patient name updated",
            extra={"event": "patient.name.updated", "patient_id": patient_id, "name_id": name_id},
        )
        return updated

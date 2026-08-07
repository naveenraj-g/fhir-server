from app.core.logging import get_logger
from app.errors.domain import NotFoundError
from app.models.patient import PatientModel
from app.schemas.patient import LinkCreate, LinkPatch


logger = get_logger(__name__)


class _LinkMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.link rows. Every
    method validates the parent patient via get_patient_scoped() first."""

    async def add_link(
        self,
        patient_id: int,
        payload: LinkCreate,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Append one patient-link row to this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.add_link(patient_id, payload, created_by)
        if not updated:
            raise NotFoundError("Patient not found")
        logger.info(
            "Patient link added",
            extra={"event": "patient.link.added", "patient_id": patient_id},
        )
        return updated

    async def get_links(self, patient_id: int, org_id: str | None = None) -> list:
        """All patient-link rows for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_links(patient_id)

    async def delete_link(
        self, patient_id: int, link_id: int, org_id: str | None = None
    ) -> None:
        """Delete one patient-link row."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_link(patient_id, link_id)
        if not deleted:
            raise NotFoundError("Link not found on this Patient")
        logger.info(
            "Patient link deleted",
            extra={"event": "patient.link.deleted", "patient_id": patient_id, "link_id": link_id},
        )

    async def patch_link(
        self,
        patient_id: int,
        link_id: int,
        payload: LinkPatch,
        org_id: str | None = None,
        updated_by: str | None = None,
    ) -> PatientModel:
        """Partial update of one patient-link row."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.patch_link(
            patient_id, link_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Link not found on this Patient")
        logger.info(
            "Patient link updated",
            extra={"event": "patient.link.updated", "patient_id": patient_id, "link_id": link_id},
        )
        return updated

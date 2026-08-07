from app.core.logging import get_logger
from app.errors.domain import NotFoundError
from app.models.patient import PatientModel
from app.schemas.patient import ContactCreate, ContactPatch


logger = get_logger(__name__)


class _ContactMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.contact rows.
    Every method validates the parent patient via get_patient_scoped() first."""

    async def add_contact(
        self,
        patient_id: int,
        payload: ContactCreate,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Append one contact row (plus its relationship[]/telecom[] grandchildren) to this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.add_contact(patient_id, payload, created_by)
        if not updated:
            raise NotFoundError("Patient not found")
        logger.info(
            "Patient contact added",
            extra={"event": "patient.contact.added", "patient_id": patient_id},
        )
        return updated

    async def get_contacts(self, patient_id: int, org_id: str | None = None) -> list:
        """All contact rows (with grandchildren eager-loaded) for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_contacts(patient_id)

    async def delete_contact(
        self, patient_id: int, contact_id: int, org_id: str | None = None
    ) -> None:
        """Delete one contact row (cascades to its grandchildren)."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_contact(patient_id, contact_id)
        if not deleted:
            raise NotFoundError("Contact not found on this Patient")
        logger.info(
            "Patient contact deleted",
            extra={"event": "patient.contact.deleted", "patient_id": patient_id, "contact_id": contact_id},
        )

    async def patch_contact(
        self,
        patient_id: int,
        contact_id: int,
        payload: ContactPatch,
        org_id: str | None = None,
        updated_by: str | None = None,
    ) -> PatientModel:
        """Partial update of one contact row — replaces relationship[]/telecom[] wholesale if supplied."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.patch_contact(
            patient_id, contact_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Contact not found on this Patient")
        logger.info(
            "Patient contact updated",
            extra={"event": "patient.contact.updated", "patient_id": patient_id, "contact_id": contact_id},
        )
        return updated

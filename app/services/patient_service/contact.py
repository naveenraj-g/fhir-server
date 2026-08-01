from app.errors.domain import NotFoundError
from app.models.patient.patient import PatientModel
from app.schemas.patient import ContactCreate, ContactPatch


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
        return updated

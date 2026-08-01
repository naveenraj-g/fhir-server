from app.errors.domain import NotFoundError
from app.models.patient.patient import PatientModel
from app.schemas.patient import AddressCreate, AddressPatch


class _AddressMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.address rows.
    Every method validates the parent patient via get_patient_scoped() first."""

    async def add_address(
        self,
        patient_id: int,
        payload: AddressCreate,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Append one address row to this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.add_address(patient_id, payload, created_by)
        if not updated:
            raise NotFoundError("Patient not found")
        return updated

    async def get_addresses(self, patient_id: int, org_id: str | None = None) -> list:
        """All address rows for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_addresses(patient_id)

    async def delete_address(
        self, patient_id: int, address_id: int, org_id: str | None = None
    ) -> None:
        """Delete one address row."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_address(patient_id, address_id)
        if not deleted:
            raise NotFoundError("Address not found on this Patient")

    async def patch_address(
        self,
        patient_id: int,
        address_id: int,
        payload: AddressPatch,
        org_id: str | None = None,
        updated_by: str | None = None,
    ) -> PatientModel:
        """Partial update of one address row."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.patch_address(
            patient_id, address_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Address not found on this Patient")
        return updated

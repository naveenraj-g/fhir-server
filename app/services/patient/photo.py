from app.errors.domain import NotFoundError
from app.models.patient import PatientModel
from app.schemas.patient import PhotoCreate, PhotoPatch


class _PhotoMixin:
    """Full lifecycle (add/list/delete/patch) for Patient.photo rows.
    Every method validates the parent patient via get_patient_scoped() first."""

    async def add_photo(
        self,
        patient_id: int,
        payload: PhotoCreate,
        org_id: str | None = None,
        created_by: str | None = None,
    ) -> PatientModel:
        """Append one photo attachment row to this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.add_photo(patient_id, payload, created_by)
        if not updated:
            raise NotFoundError("Patient not found")
        return updated

    async def get_photos(self, patient_id: int, org_id: str | None = None) -> list:
        """All photo attachment rows for this patient."""
        await self.get_patient_scoped(patient_id, org_id)
        return await self.repository.get_photos(patient_id)

    async def delete_photo(
        self, patient_id: int, photo_id: int, org_id: str | None = None
    ) -> None:
        """Delete one photo attachment row."""
        await self.get_patient_scoped(patient_id, org_id)
        deleted = await self.repository.delete_photo(patient_id, photo_id)
        if not deleted:
            raise NotFoundError("Photo not found on this Patient")

    async def patch_photo(
        self,
        patient_id: int,
        photo_id: int,
        payload: PhotoPatch,
        org_id: str | None = None,
        updated_by: str | None = None,
    ) -> PatientModel:
        """Partial update of one photo attachment row."""
        await self.get_patient_scoped(patient_id, org_id)
        updated = await self.repository.patch_photo(
            patient_id, photo_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Photo not found on this Patient")
        return updated

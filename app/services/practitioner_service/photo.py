from typing import Optional

from app.errors.domain import NotFoundError
from app.models.practitioner import PractitionerModel
from app.schemas.practitioner import PractitionerPhotoCreate, PractitionerPhotoPatch


class _PhotoMixin:
    """Full lifecycle (add/list/delete/patch) for Practitioner.photo rows.
    Every method validates the parent practitioner via get_practitioner_scoped() first."""

    async def add_photo(
        self, practitioner_id: int, payload: PractitionerPhotoCreate,
        org_id: Optional[str] = None, created_by: Optional[str] = None,
    ) -> PractitionerModel:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        updated = await self.repository.add_photo(practitioner_id, payload, created_by)
        if not updated:
            raise NotFoundError("Practitioner not found")
        return updated

    async def get_photos(self, practitioner_id: int, org_id: Optional[str] = None) -> list:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        return await self.repository.get_photos(practitioner_id)

    async def delete_photo(
        self, practitioner_id: int, photo_id: int, org_id: Optional[str] = None
    ) -> None:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        deleted = await self.repository.delete_photo(practitioner_id, photo_id)
        if not deleted:
            raise NotFoundError("Photo not found on this Practitioner")

    async def patch_photo(
        self, practitioner_id: int, photo_id: int, payload: PractitionerPhotoPatch,
        org_id: Optional[str] = None, updated_by: Optional[str] = None,
    ) -> PractitionerModel:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        updated = await self.repository.patch_photo(practitioner_id, photo_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Photo not found on this Practitioner")
        return updated

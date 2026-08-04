from typing import Optional

from app.errors.domain import NotFoundError
from app.models.practitioner import PractitionerModel
from app.schemas.practitioner import PractitionerQualificationCreate, PractitionerQualificationPatch


class _QualificationMixin:
    """Full lifecycle (add/list/delete/patch) for Practitioner.qualification
    rows. Every method validates the parent practitioner via
    get_practitioner_scoped() first."""

    async def add_qualification(
        self, practitioner_id: int, payload: PractitionerQualificationCreate,
        org_id: Optional[str] = None, created_by: Optional[str] = None,
    ) -> PractitionerModel:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        updated = await self.repository.add_qualification(practitioner_id, payload, created_by)
        if not updated:
            raise NotFoundError("Practitioner not found")
        return updated

    async def get_qualifications(self, practitioner_id: int, org_id: Optional[str] = None) -> list:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        return await self.repository.get_qualifications(practitioner_id)

    async def delete_qualification(
        self, practitioner_id: int, qualification_id: int, org_id: Optional[str] = None
    ) -> None:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        deleted = await self.repository.delete_qualification(practitioner_id, qualification_id)
        if not deleted:
            raise NotFoundError("Qualification not found on this Practitioner")

    async def patch_qualification(
        self, practitioner_id: int, qualification_id: int, payload: PractitionerQualificationPatch,
        org_id: Optional[str] = None, updated_by: Optional[str] = None,
    ) -> PractitionerModel:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        updated = await self.repository.patch_qualification(
            practitioner_id, qualification_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Qualification not found on this Practitioner")
        return updated

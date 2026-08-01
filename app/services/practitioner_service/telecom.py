from typing import Optional

from app.errors.domain import NotFoundError
from app.models.practitioner import PractitionerModel
from app.schemas.practitioner import PractitionerTelecomCreate, PractitionerTelecomPatch


class _TelecomMixin:
    """Full lifecycle (add/list/delete/patch) for Practitioner.telecom rows.
    Every method validates the parent practitioner via get_practitioner_scoped() first."""

    async def add_telecom(
        self, practitioner_id: int, payload: PractitionerTelecomCreate,
        org_id: Optional[str] = None, created_by: Optional[str] = None,
    ) -> PractitionerModel:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        updated = await self.repository.add_telecom(practitioner_id, payload, created_by)
        if not updated:
            raise NotFoundError("Practitioner not found")
        return updated

    async def get_telecoms(self, practitioner_id: int, org_id: Optional[str] = None) -> list:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        return await self.repository.get_telecoms(practitioner_id)

    async def delete_telecom(
        self, practitioner_id: int, telecom_id: int, org_id: Optional[str] = None
    ) -> None:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        deleted = await self.repository.delete_telecom(practitioner_id, telecom_id)
        if not deleted:
            raise NotFoundError("Telecom not found on this Practitioner")

    async def patch_telecom(
        self, practitioner_id: int, telecom_id: int, payload: PractitionerTelecomPatch,
        org_id: Optional[str] = None, updated_by: Optional[str] = None,
    ) -> PractitionerModel:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        updated = await self.repository.patch_telecom(practitioner_id, telecom_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Telecom not found on this Practitioner")
        return updated

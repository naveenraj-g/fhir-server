from typing import Optional

from app.errors.domain import NotFoundError
from app.models.practitioner import PractitionerModel
from app.schemas.practitioner import PractitionerAddressCreate, PractitionerAddressPatch


class _AddressMixin:
    """Full lifecycle (add/list/delete/patch) for Practitioner.address rows.
    Every method validates the parent practitioner via get_practitioner_scoped() first."""

    async def add_address(
        self, practitioner_id: int, payload: PractitionerAddressCreate,
        org_id: Optional[str] = None, created_by: Optional[str] = None,
    ) -> PractitionerModel:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        updated = await self.repository.add_address(practitioner_id, payload, created_by)
        if not updated:
            raise NotFoundError("Practitioner not found")
        return updated

    async def get_addresses(self, practitioner_id: int, org_id: Optional[str] = None) -> list:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        return await self.repository.get_addresses(practitioner_id)

    async def delete_address(
        self, practitioner_id: int, address_id: int, org_id: Optional[str] = None
    ) -> None:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        deleted = await self.repository.delete_address(practitioner_id, address_id)
        if not deleted:
            raise NotFoundError("Address not found on this Practitioner")

    async def patch_address(
        self, practitioner_id: int, address_id: int, payload: PractitionerAddressPatch,
        org_id: Optional[str] = None, updated_by: Optional[str] = None,
    ) -> PractitionerModel:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        updated = await self.repository.patch_address(practitioner_id, address_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Address not found on this Practitioner")
        return updated

from typing import Optional

from app.errors.domain import NotFoundError
from app.models.practitioner import PractitionerModel
from app.schemas.practitioner import PractitionerIdentifierCreate, PractitionerIdentifierPatch


class _IdentifierMixin:
    """Full lifecycle (add/list/delete/patch) for Practitioner.identifier rows.
    Every method validates the parent practitioner via get_practitioner_scoped() first."""

    async def add_identifier(
        self, practitioner_id: int, payload: PractitionerIdentifierCreate,
        org_id: Optional[str] = None, created_by: Optional[str] = None,
    ) -> PractitionerModel:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        updated = await self.repository.add_identifier(practitioner_id, payload, created_by)
        if not updated:
            raise NotFoundError("Practitioner not found")
        return updated

    async def get_identifiers(self, practitioner_id: int, org_id: Optional[str] = None) -> list:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        return await self.repository.get_identifiers(practitioner_id)

    async def delete_identifier(
        self, practitioner_id: int, identifier_id: int, org_id: Optional[str] = None
    ) -> None:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        deleted = await self.repository.delete_identifier(practitioner_id, identifier_id)
        if not deleted:
            raise NotFoundError("Identifier not found on this Practitioner")

    async def patch_identifier(
        self, practitioner_id: int, identifier_id: int, payload: PractitionerIdentifierPatch,
        org_id: Optional[str] = None, updated_by: Optional[str] = None,
    ) -> PractitionerModel:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        updated = await self.repository.patch_identifier(
            practitioner_id, identifier_id, payload, updated_by
        )
        if not updated:
            raise NotFoundError("Identifier not found on this Practitioner")
        return updated

from typing import Optional

from app.core.logging import get_logger
from app.errors.domain import NotFoundError
from app.models.practitioner import PractitionerModel
from app.schemas.practitioner import PractitionerNameCreate, PractitionerNamePatch


logger = get_logger(__name__)


class _NameMixin:
    """Full lifecycle (add/list/delete/patch) for Practitioner.name rows.
    Every method validates the parent practitioner via get_practitioner_scoped() first."""

    async def add_name(
        self, practitioner_id: int, payload: PractitionerNameCreate,
        org_id: Optional[str] = None, created_by: Optional[str] = None,
    ) -> PractitionerModel:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        updated = await self.repository.add_name(practitioner_id, payload, created_by)
        if not updated:
            raise NotFoundError("Practitioner not found")
        logger.info(
            "Practitioner name added",
            extra={"event": "practitioner.name.added", "practitioner_id": practitioner_id},
        )
        return updated

    async def get_names(self, practitioner_id: int, org_id: Optional[str] = None) -> list:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        return await self.repository.get_names(practitioner_id)

    async def delete_name(
        self, practitioner_id: int, name_id: int, org_id: Optional[str] = None
    ) -> None:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        deleted = await self.repository.delete_name(practitioner_id, name_id)
        if not deleted:
            raise NotFoundError("Name not found on this Practitioner")
        logger.info(
            "Practitioner name deleted",
            extra={"event": "practitioner.name.deleted", "practitioner_id": practitioner_id, "name_id": name_id},
        )

    async def patch_name(
        self, practitioner_id: int, name_id: int, payload: PractitionerNamePatch,
        org_id: Optional[str] = None, updated_by: Optional[str] = None,
    ) -> PractitionerModel:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        updated = await self.repository.patch_name(practitioner_id, name_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Name not found on this Practitioner")
        logger.info(
            "Practitioner name updated",
            extra={"event": "practitioner.name.updated", "practitioner_id": practitioner_id, "name_id": name_id},
        )
        return updated

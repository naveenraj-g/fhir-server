from typing import Optional

from app.core.logging import get_logger
from app.errors.domain import NotFoundError
from app.models.practitioner import PractitionerModel
from app.schemas.practitioner import PractitionerTelecomCreate, PractitionerTelecomPatch


logger = get_logger(__name__)


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
        logger.info(
            "Practitioner telecom added",
            extra={"event": "practitioner.telecom.added", "practitioner_id": practitioner_id},
        )
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
        logger.info(
            "Practitioner telecom deleted",
            extra={"event": "practitioner.telecom.deleted", "practitioner_id": practitioner_id, "telecom_id": telecom_id},
        )

    async def patch_telecom(
        self, practitioner_id: int, telecom_id: int, payload: PractitionerTelecomPatch,
        org_id: Optional[str] = None, updated_by: Optional[str] = None,
    ) -> PractitionerModel:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        updated = await self.repository.patch_telecom(practitioner_id, telecom_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Telecom not found on this Practitioner")
        logger.info(
            "Practitioner telecom updated",
            extra={"event": "practitioner.telecom.updated", "practitioner_id": practitioner_id, "telecom_id": telecom_id},
        )
        return updated

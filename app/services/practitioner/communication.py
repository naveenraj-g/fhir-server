from typing import Optional

from app.core.logging import get_logger
from app.errors.domain import NotFoundError
from app.models.practitioner import PractitionerModel
from app.schemas.practitioner import PractitionerCommunicationCreate, PractitionerCommunicationPatch


logger = get_logger(__name__)


class _CommunicationMixin:
    """Full lifecycle (add/list/delete/patch) for Practitioner.communication
    rows. Every method validates the parent practitioner via
    get_practitioner_scoped() first."""

    async def add_communication(
        self, practitioner_id: int, payload: PractitionerCommunicationCreate,
        org_id: Optional[str] = None, created_by: Optional[str] = None,
    ) -> PractitionerModel:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        updated = await self.repository.add_communication(practitioner_id, payload, created_by)
        if not updated:
            raise NotFoundError("Practitioner not found")
        logger.info(
            "Practitioner communication added",
            extra={"event": "practitioner.communication.added", "practitioner_id": practitioner_id},
        )
        return updated

    async def get_communications(self, practitioner_id: int, org_id: Optional[str] = None) -> list:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        return await self.repository.get_communications(practitioner_id)

    async def delete_communication(
        self, practitioner_id: int, comm_id: int, org_id: Optional[str] = None
    ) -> None:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        deleted = await self.repository.delete_communication(practitioner_id, comm_id)
        if not deleted:
            raise NotFoundError("Communication not found on this Practitioner")
        logger.info(
            "Practitioner communication deleted",
            extra={"event": "practitioner.communication.deleted", "practitioner_id": practitioner_id, "comm_id": comm_id},
        )

    async def patch_communication(
        self, practitioner_id: int, comm_id: int, payload: PractitionerCommunicationPatch,
        org_id: Optional[str] = None, updated_by: Optional[str] = None,
    ) -> PractitionerModel:
        await self.get_practitioner_scoped(practitioner_id, org_id)
        updated = await self.repository.patch_communication(practitioner_id, comm_id, payload, updated_by)
        if not updated:
            raise NotFoundError("Communication not found on this Practitioner")
        logger.info(
            "Practitioner communication updated",
            extra={"event": "practitioner.communication.updated", "practitioner_id": practitioner_id, "comm_id": comm_id},
        )
        return updated

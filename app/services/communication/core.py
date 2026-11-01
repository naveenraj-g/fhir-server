from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.communication import (
    merge_patch_fragment,
    patch_fragment_to_fhir_communication,
    payload_to_fhir_communication,
    to_fhir_communication,
    to_plain_communication,
)
from app.fhir.validation import validate_resource
from app.models.communication import CommunicationModel
from app.repository.communication import CommunicationRepository
from app.schemas.communication import (
    CommunicationCreateSchema,
    CommunicationPatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All Communication business logic."""

    def __init__(self, repository: CommunicationRepository):
        self.repository = repository

    def _to_fhir(self, model: CommunicationModel) -> dict:
        return to_fhir_communication(model)

    def _to_plain(self, model: CommunicationModel) -> dict:
        return to_plain_communication(model)

    async def get_communication_scoped(
        self, communication_id: int, org_id: str | None
    ) -> CommunicationModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "Communication operation requires an org-scoped token"
            )
        model = await self.repository.get_by_communication_id_in_org(
            communication_id, org_id
        )
        if not model:
            raise NotFoundError("Communication not found")
        return model

    async def list_communications(
        self,
        org_id: str | None = None,
        subject: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        encounter: str | None = None,
        sender: str | None = None,
        recipient: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[int, list[CommunicationModel]]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "Communication operation requires an org-scoped token"
            )
        total, items = await self.repository.list(
            org_id=org_id,
            subject=subject,
            status=status,
            priority=priority,
            encounter=encounter,
            sender=sender,
            recipient=recipient,
            limit=limit,
            offset=offset,
            sort=sort,
        )
        return total, items

    async def create_communication(
        self,
        payload: CommunicationCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> CommunicationModel:
        if not org_id:
            raise PermissionDeniedError(
                "Communication creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "Communication creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_communication(payload), org_id
        )

        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "Communication created",
            extra={
                "event": "communication.created",
                "communication_id": model.communication_id,
            },
        )
        return model

    async def patch_communication(
        self,
        communication_id: int,
        payload: CommunicationPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> CommunicationModel:
        if not org_id:
            self._log_org_scope_miss(
                "patch", communication_id, org_id
            )
            raise NotFoundError("Communication not found")
        existing = await self.repository.get_by_communication_id_in_org(
            communication_id, org_id
        )
        if not existing:
            self._log_org_scope_miss(
                "patch", communication_id, org_id
            )
            raise NotFoundError("Communication not found")

        if not updated_by:
            raise PermissionDeniedError(
                "Communication modification requires an authenticated actor"
            )

        fragment, touched = patch_fragment_to_fhir_communication(payload)
        current_fhir = self._to_fhir(existing)
        merged = merge_patch_fragment(current_fhir, fragment, touched)
        await self._validate_base_r4(merged, org_id)

        model = await self.repository.patch_full(
            communication_id,
            payload,
            org_id=org_id,
            updated_by=updated_by,
        )
        logger.info(
            "Communication patched",
            extra={
                "event": "communication.patched",
                "communication_id": communication_id,
            },
        )
        return model

    async def delete_communication(
        self, communication_id: int, org_id: str | None = None
    ) -> None:
        if not org_id:
            self._log_org_scope_miss(
                "delete", communication_id, org_id
            )
            raise NotFoundError("Communication not found")
        if not await self.repository.communication_belongs_to_org(
            communication_id, org_id
        ):
            self._log_org_scope_miss(
                "delete", communication_id, org_id
            )
            raise NotFoundError("Communication not found")
        deleted = await self.repository.delete(
            communication_id, org_id=org_id
        )
        if not deleted:
            raise NotFoundError("Communication not found")
        logger.info(
            "Communication deleted",
            extra={
                "event": "communication.deleted",
                "communication_id": communication_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "Communication", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "Communication failed base R4 validation",
                extra={
                    "event": "communication.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, communication_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "Communication write rejected by org scope",
            extra={
                "event": "communication.org_scope_miss",
                "operation": operation,
                "communication_id": communication_id,
                "org_id": org_id,
            },
        )


class CommunicationService(_CoreMixin):
    """Service orchestrating Communication operations."""
    pass

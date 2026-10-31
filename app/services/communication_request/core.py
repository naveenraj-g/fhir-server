from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.communication_request import (
    merge_patch_fragment,
    patch_fragment_to_fhir_communication_request,
    payload_to_fhir_communication_request,
    to_fhir_communication_request,
    to_plain_communication_request,
)
from app.fhir.validation import validate_resource
from app.models.communication_request import CommunicationRequestModel
from app.repository.communication_request import CommunicationRequestRepository
from app.schemas.communication_request import (
    CommunicationRequestCreateSchema,
    CommunicationRequestPatchSchema,
)

logger = get_logger(__name__)


class _CoreMixin:
    """All CommunicationRequest business logic."""

    def __init__(self, repository: CommunicationRequestRepository):
        self.repository = repository

    def _to_fhir(self, model: CommunicationRequestModel) -> dict:
        return to_fhir_communication_request(model)

    def _to_plain(self, model: CommunicationRequestModel) -> dict:
        return to_plain_communication_request(model)

    async def get_communication_request_scoped(
        self, communication_request_id: int, org_id: str | None
    ) -> CommunicationRequestModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError(
                "CommunicationRequest operation requires an org-scoped token"
            )
        model = await self.repository.get_by_communication_request_id_in_org(
            communication_request_id, org_id
        )
        if not model:
            raise NotFoundError("CommunicationRequest not found")
        return model

    async def list_communication_requests(
        self,
        org_id: str | None = None,
        subject: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        encounter: str | None = None,
        requester: str | None = None,
        sender: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
    ) -> tuple[int, list[CommunicationRequestModel]]:
        """Raises PermissionDeniedError (403) for an org-less token."""
        if not org_id:
            raise PermissionDeniedError(
                "CommunicationRequest operation requires an org-scoped token"
            )
        items, total = await self.repository.list(
            org_id=org_id,
            subject=subject,
            status=status,
            priority=priority,
            encounter=encounter,
            requester=requester,
            sender=sender,
            limit=limit,
            offset=offset,
            sort=sort,
        )
        return total, items

    async def create_communication_request(
        self,
        payload: CommunicationRequestCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> CommunicationRequestModel:
        if not org_id:
            raise PermissionDeniedError(
                "CommunicationRequest creation requires an org-scoped token"
            )
        if not created_by:
            raise PermissionDeniedError(
                "CommunicationRequest creation requires an authenticated actor"
            )

        await self._validate_base_r4(
            payload_to_fhir_communication_request(payload), org_id
        )

        model = await self.repository.create_full(
            payload, org_id, created_by
        )
        logger.info(
            "CommunicationRequest created",
            extra={
                "event": "communication_request.created",
                "communication_request_id": model.communication_request_id,
            },
        )
        return model

    async def patch_communication_request(
        self,
        communication_request_id: int,
        payload: CommunicationRequestPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> CommunicationRequestModel:
        if not org_id:
            self._log_org_scope_miss(
                "patch", communication_request_id, org_id
            )
            raise NotFoundError("CommunicationRequest not found")
        existing = await self.repository.get_by_communication_request_id_in_org(
            communication_request_id, org_id
        )
        if not existing:
            self._log_org_scope_miss(
                "patch", communication_request_id, org_id
            )
            raise NotFoundError("CommunicationRequest not found")

        if not updated_by:
            raise PermissionDeniedError(
                "CommunicationRequest modification requires an authenticated actor"
            )

        fragment, touched = patch_fragment_to_fhir_communication_request(payload)
        current_fhir = self._to_fhir(existing)
        merged = merge_patch_fragment(current_fhir, fragment, touched)
        await self._validate_base_r4(merged, org_id)

        model = await self.repository.patch_full(
            communication_request_id,
            payload,
            org_id=org_id,
            updated_by=updated_by,
        )
        logger.info(
            "CommunicationRequest patched",
            extra={
                "event": "communication_request.patched",
                "communication_request_id": communication_request_id,
            },
        )
        return model

    async def delete_communication_request(
        self, communication_request_id: int, org_id: str | None = None
    ) -> None:
        if not org_id:
            self._log_org_scope_miss(
                "delete", communication_request_id, org_id
            )
            raise NotFoundError("CommunicationRequest not found")
        if not await self.repository.communication_request_belongs_to_org(
            communication_request_id, org_id
        ):
            self._log_org_scope_miss(
                "delete", communication_request_id, org_id
            )
            raise NotFoundError("CommunicationRequest not found")
        deleted = await self.repository.delete(
            communication_request_id, org_id=org_id
        )
        if not deleted:
            raise NotFoundError("CommunicationRequest not found")
        logger.info(
            "CommunicationRequest deleted",
            extra={
                "event": "communication_request.deleted",
                "communication_request_id": communication_request_id,
            },
        )

    @staticmethod
    async def _validate_base_r4(
        fhir_resource: dict, org_id: str | None = None
    ) -> None:
        errors = await validate_resource(
            "CommunicationRequest", fhir_resource, org_id=org_id
        )
        if errors:
            logger.warning(
                "CommunicationRequest failed base R4 validation",
                extra={
                    "event": "communication_request.base_r4_invalid",
                    "errors": errors,
                },
            )
            raise FhirValidationError(errors)

    @staticmethod
    def _log_org_scope_miss(
        operation: str, communication_request_id: int, org_id: str | None
    ) -> None:
        logger.warning(
            "CommunicationRequest write rejected by org scope",
            extra={
                "event": "communication_request.org_scope_miss",
                "operation": operation,
                "communication_request_id": communication_request_id,
                "org_id": org_id,
            },
        )


class CommunicationRequestService(_CoreMixin):
    """Service orchestrating CommunicationRequest operations."""
    pass

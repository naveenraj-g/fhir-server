from app.core.logging import get_logger
from app.errors.domain import NotFoundError
from app.errors.validation import FhirValidationError
from app.fhir.mappers.service_request import (
    merge_patch_fragment,
    patch_fragment_to_fhir_service_request,
    payload_to_fhir_service_request,
    to_fhir_service_request,
    to_plain_service_request,
)
from app.fhir.validation import validate_resource
from app.models.service_request import (
    ServiceRequestIntent as ServiceRequestIntentModel,
    ServiceRequestModel,
    ServiceRequestStatus as ServiceRequestStatusModel,
)
from app.repository.service_request import ServiceRequestRepository
from app.schemas.enums import ServiceRequestIntent, ServiceRequestStatus
from app.schemas.service_request import ServiceRequestCreateSchema, ServiceRequestPatchSchema

logger = get_logger(__name__)


class _CoreMixin:
    """All ServiceRequest business logic. Default (gateway-trusted)
    pattern — same as QuestionnaireResponse: no org-scoped existence
    check or ownership enforcement at all."""

    def __init__(self, repository: ServiceRequestRepository):
        self.repository = repository

    def _to_fhir(self, service_request: ServiceRequestModel) -> dict:
        return to_fhir_service_request(service_request)

    def _to_plain(self, service_request: ServiceRequestModel) -> dict:
        return to_plain_service_request(service_request)

    async def get_by_service_request_id(self, service_request_id: int) -> ServiceRequestModel:
        service_request = await self.repository.get_by_service_request_id(service_request_id)
        if not service_request:
            raise NotFoundError("ServiceRequest not found")
        return service_request

    async def get_me(
        self,
        user_id: str,
        tenant_id: str | None = None,
        status: ServiceRequestStatus | None = None,
        intent: ServiceRequestIntent | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ServiceRequestModel], int | None]:
        return await self.repository.get_me(
            user_id=user_id,
            tenant_id=tenant_id,
            status=ServiceRequestStatusModel[status.name] if status else None,
            intent=ServiceRequestIntentModel[intent.name] if intent else None,
            subject=subject,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def list_service_requests(
        self,
        tenant_id: str | None = None,
        user_id: str | None = None,
        status: ServiceRequestStatus | None = None,
        intent: ServiceRequestIntent | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ServiceRequestModel], int | None]:
        return await self.repository.list(
            tenant_id=tenant_id,
            user_id=user_id,
            status=ServiceRequestStatusModel[status.name] if status else None,
            intent=ServiceRequestIntentModel[intent.name] if intent else None,
            subject=subject,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_service_request(self, payload: ServiceRequestCreateSchema) -> ServiceRequestModel:
        await self._validate_base_r4(payload_to_fhir_service_request(payload), payload.tenant_id)
        service_request = await self.repository.create_full(payload)
        logger.info(
            "ServiceRequest created",
            extra={"event": "service_request.created", "service_request_id": service_request.service_request_id},
        )
        return service_request

    async def patch_service_request(
        self, service_request_id: int, payload: ServiceRequestPatchSchema
    ) -> ServiceRequestModel:
        existing = await self.repository.get_by_service_request_id(service_request_id)
        if not existing:
            raise NotFoundError("ServiceRequest not found")

        fragment, touched = patch_fragment_to_fhir_service_request(payload)
        merged = merge_patch_fragment(to_fhir_service_request(existing), fragment, touched)
        await self._validate_base_r4(merged, existing.tenant_id)

        updated = await self.repository.patch_full(service_request_id, payload)
        if not updated:
            raise NotFoundError("ServiceRequest not found")
        logger.info(
            "ServiceRequest updated",
            extra={
                "event": "service_request.updated",
                "service_request_id": service_request_id,
                "fields": sorted(payload.model_dump(exclude_unset=True).keys()),
            },
        )
        return updated

    async def delete_service_request(self, service_request_id: int) -> None:
        deleted = await self.repository.delete(service_request_id)
        if not deleted:
            raise NotFoundError("ServiceRequest not found")
        logger.info(
            "ServiceRequest deleted",
            extra={"event": "service_request.deleted", "service_request_id": service_request_id},
        )

    @staticmethod
    async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
        errors = await validate_resource("ServiceRequest", fhir_resource, org_id=org_id)
        if errors:
            logger.warning(
                "ServiceRequest failed base R4 validation",
                extra={"event": "service_request.base_r4_invalid", "errors": errors},
            )
            raise FhirValidationError(errors)

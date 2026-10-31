from app.core.logging import get_logger
from app.errors.auth import PermissionDeniedError
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
    """All ServiceRequest business logic. Auth matches Questionnaire/
    QuestionnaireResponse: tenant scoping comes from the verified JWT's
    activeOrganizationId claim (actor.org_id), never a client-suppliable
    field, and there's no org-less/super-admin bypass — every operation
    requires an org-scoped actor. `user_id` is a plain,
    gateway-forwarded field."""

    def __init__(self, repository: ServiceRequestRepository):
        self.repository = repository

    def _to_fhir(self, service_request: ServiceRequestModel) -> dict:
        return to_fhir_service_request(service_request)

    def _to_plain(self, service_request: ServiceRequestModel) -> dict:
        return to_plain_service_request(service_request)

    async def get_service_request_scoped(
        self, service_request_id: int, org_id: str | None
    ) -> ServiceRequestModel:
        """Requires an org-scoped actor — raises PermissionDeniedError (403)
        for an org-less token instead of silently falling back to an
        unscoped lookup, then NotFoundError (404, never 403) if it belongs
        to a different org, so existence isn't leaked."""
        if not org_id:
            raise PermissionDeniedError("ServiceRequest operation requires an org-scoped token")
        service_request = await self.repository.get_by_service_request_id_in_org(
            service_request_id, org_id
        )
        if not service_request:
            raise NotFoundError("ServiceRequest not found")
        return service_request

    async def list_service_requests(
        self,
        org_id: str | None = None,
        status: ServiceRequestStatus | None = None,
        intent: ServiceRequestIntent | None = None,
        subject: str | None = None,
        identifier: str | None = None,
        limit: int = 50,
        offset: int = 0,
        sort: str | None = None,
        total_mode: str = "accurate",
    ) -> tuple[list[ServiceRequestModel], int | None]:
        """Raises PermissionDeniedError (403) for an org-less token — same
        invariant as get_service_request_scoped()."""
        if not org_id:
            raise PermissionDeniedError("ServiceRequest operation requires an org-scoped token")
        return await self.repository.list(
            org_id=org_id,
            status=ServiceRequestStatusModel[status.name] if status else None,
            intent=ServiceRequestIntentModel[intent.name] if intent else None,
            subject=subject,
            identifier=identifier,
            limit=limit,
            offset=offset,
            sort=sort,
            total_mode=total_mode,
        )

    async def create_service_request(
        self,
        payload: ServiceRequestCreateSchema,
        org_id: str | None,
        created_by: str | None,
    ) -> ServiceRequestModel:
        """org_id comes from the verified JWT's actor.org_id, not a client-
        supplied field — there is no bypass, so an org-less/platform token
        cannot create a ServiceRequest at all."""
        if not org_id:
            raise PermissionDeniedError("ServiceRequest creation requires an org-scoped token")
        await self._validate_base_r4(payload_to_fhir_service_request(payload), org_id)
        service_request = await self.repository.create_full(payload, org_id, created_by)
        logger.info(
            "ServiceRequest created",
            extra={"event": "service_request.created", "service_request_id": service_request.service_request_id},
        )
        return service_request

    async def patch_service_request(
        self,
        service_request_id: int,
        payload: ServiceRequestPatchSchema,
        updated_by: str | None = None,
        org_id: str | None = None,
    ) -> ServiceRequestModel:
        """org_id comes from the verified JWT's actor.org_id — no bypass: a
        missing org_id or a resource belonging to a different org both
        raise NotFoundError (404), never 403, so existence isn't leaked."""
        if not org_id:
            self._log_org_scope_miss("patch", service_request_id, org_id)
            raise NotFoundError("ServiceRequest not found")
        existing = await self.repository.get_by_service_request_id_in_org(service_request_id, org_id)
        if not existing:
            self._log_org_scope_miss("patch", service_request_id, org_id)
            raise NotFoundError("ServiceRequest not found")

        fragment, touched = patch_fragment_to_fhir_service_request(payload)
        merged = merge_patch_fragment(to_fhir_service_request(existing), fragment, touched)
        await self._validate_base_r4(merged, org_id)

        updated = await self.repository.patch_full(service_request_id, payload, updated_by)
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

    async def delete_service_request(self, service_request_id: int, org_id: str | None = None) -> None:
        """Same org_id ownership gate as patch_service_request."""
        if not org_id or not await self.repository.service_request_belongs_to_org(
            service_request_id, org_id
        ):
            self._log_org_scope_miss("delete", service_request_id, org_id)
            raise NotFoundError("ServiceRequest not found")
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

    @staticmethod
    def _log_org_scope_miss(operation: str, service_request_id: int, org_id: str | None) -> None:
        """The tenant gate rejected a write. The caller gets a plain 404 —
        deliberately indistinguishable from "no such resource" — so this
        log line is the only place the distinction is recorded."""
        logger.warning(
            "ServiceRequest write rejected by org scope",
            extra={
                "event": "service_request.org_scope_miss",
                "operation": operation,
                "service_request_id": service_request_id,
                "reason": "no_org_token" if not org_id else "different_org",
            },
        )

from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.deps.service_request_deps import resolve_service_request
from app.di.dependencies.service_request import get_service_request_service
from app.models.service_request import ServiceRequestModel
from app.schemas.enums import ServiceRequestIntent, ServiceRequestStatus
from app.schemas.service_request import ServiceRequestCreateSchema, ServiceRequestPatchSchema
from app.services.service_request import ServiceRequestService

from ._responses import _CONTENT_NEG, _ERR_NOT_FOUND, _ERR_VALIDATION, _LIST_200, _SINGLE_200, _SINGLE_201

router = APIRouter()

logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_service_request",
    summary="Create a new ServiceRequest resource",
    description=(
        "A record of a request for a procedure or diagnostic/other service to be performed. "
        "Accepts the full nested payload atomically in one DB transaction. Default "
        "(gateway-trusted) pattern: `tenant_id`/`created_by` are plain request body fields. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_service_request(
    payload: ServiceRequestCreateSchema,
    request: Request,
    service_request_service: ServiceRequestService = Depends(get_service_request_service),
):
    logger.info("Create a new ServiceRequest resource", extra={"event": "route.create_service_request"})
    log_payload(logger, "service_request.create.payload", payload)
    service_request = await service_request_service.create_service_request(payload)
    return format_response(
        service_request_service._to_fhir(service_request),
        service_request_service._to_plain(service_request),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Me (must come before /{service_request_id}) ─────────────────────────────────


@router.get(
    "/me",
    operation_id="list_my_service_requests",
    summary="List ServiceRequest resources owned by a given end-user",
    description=(
        "Same filters as `GET /`, scoped to the gateway-forwarded `user_id` query param "
        "(default/gateway-trusted pattern). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_my_service_requests(
    request: Request,
    user_id: str = Query(..., description="Gateway-forwarded ID of the end-user to scope results to."),
    tenant_id: str | None = Query(None, description="Gateway-forwarded tenant/account ID."),
    service_request_status: ServiceRequestStatus | None = Query(
        None, alias="status", description="draft | active | on-hold | revoked | completed | entered-in-error | unknown."
    ),
    intent: ServiceRequestIntent | None = Query(None, description="proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option."),
    subject: str | None = Query(None, description="Exact match on the subject reference string."),
    identifier: str | None = Query(None, description="Exact match on the business identifier value."),
    params: ListParams = Depends(),
    service_request_service: ServiceRequestService = Depends(get_service_request_service),
):
    logger.info("List ServiceRequest resources owned by a given end-user", extra={"event": "route.list_my_service_requests"})
    items, total = await service_request_service.get_me(
        user_id=user_id, tenant_id=tenant_id, status=service_request_status, intent=intent,
        subject=subject, identifier=identifier, limit=params.limit, offset=params.offset,
        sort=params.sort, total_mode=params.total_mode,
    )
    return format_paginated_response(
        [service_request_service._to_fhir(sr) for sr in items],
        [service_request_service._to_plain(sr) for sr in items],
        total, params.limit, params.offset, request,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{service_request_id}",
    operation_id="get_service_request_by_id",
    summary="Retrieve a ServiceRequest resource by public service_request_id",
    description=(
        "Loaded via `resolve_service_request()` — a plain load-by-public-ID lookup with no "
        "ownership check (default/gateway-trusted pattern). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_service_request(
    request: Request,
    service_request: ServiceRequestModel = Depends(resolve_service_request),
    service_request_service: ServiceRequestService = Depends(get_service_request_service),
):
    logger.info(
        "Retrieve a ServiceRequest resource by public service_request_id",
        extra={"event": "route.get_service_request_by_id", "service_request_id": service_request.service_request_id},
    )
    return format_response(
        service_request_service._to_fhir(service_request),
        service_request_service._to_plain(service_request),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{service_request_id}",
    operation_id="patch_service_request",
    summary="Update a ServiceRequest resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list (even `[]`) atomically replaces the corresponding rows; "
        "omitted lists are left untouched. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_service_request(
    payload: ServiceRequestPatchSchema,
    request: Request,
    service_request_id: int = Path(..., ge=1, description="Public service_request identifier."),
    _existing: ServiceRequestModel = Depends(resolve_service_request),
    service_request_service: ServiceRequestService = Depends(get_service_request_service),
):
    logger.info("Update a ServiceRequest resource", extra={"event": "route.patch_service_request", "service_request_id": service_request_id})
    log_payload(logger, "service_request.patch.payload", payload)
    updated = await service_request_service.patch_service_request(service_request_id, payload)
    return format_response(
        service_request_service._to_fhir(updated),
        service_request_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_service_requests",
    summary="List all ServiceRequest resources",
    description=(
        "Returns a paginated list of ServiceRequest resources, matching a subset of the "
        "search parameters documented at https://www.hl7.org/fhir/R4/servicerequest.html#search. "
        "Filter by `status`, `intent`, `subject` (exact), `identifier` (exact business-"
        "identifier value), plus `tenant_id`/`user_id` as explicit, gateway-forwarded query "
        "filters. Sort with `sort` (e.g. `-authored_on`); set `total_mode=none` to skip the "
        "COUNT(*) on large result sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_service_requests(
    request: Request,
    tenant_id: str | None = Query(None, description="Gateway-forwarded tenant/account ID filter."),
    user_id: str | None = Query(None, description="Gateway-forwarded end-user ID filter."),
    service_request_status: ServiceRequestStatus | None = Query(
        None, alias="status", description="draft | active | on-hold | revoked | completed | entered-in-error | unknown."
    ),
    intent: ServiceRequestIntent | None = Query(None, description="proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option."),
    subject: str | None = Query(None, description="Exact match on the subject reference string."),
    identifier: str | None = Query(None, description="Exact match on the business identifier value."),
    params: ListParams = Depends(),
    service_request_service: ServiceRequestService = Depends(get_service_request_service),
):
    logger.info("List all ServiceRequest resources", extra={"event": "route.list_service_requests"})
    items, total = await service_request_service.list_service_requests(
        tenant_id=tenant_id, user_id=user_id, status=service_request_status, intent=intent,
        subject=subject, identifier=identifier, limit=params.limit, offset=params.offset,
        sort=params.sort, total_mode=params.total_mode,
    )
    return format_paginated_response(
        [service_request_service._to_fhir(sr) for sr in items],
        [service_request_service._to_plain(sr) for sr in items],
        total, params.limit, params.offset, request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{service_request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_service_request",
    summary="Delete a ServiceRequest resource",
    description="Permanently deletes the ServiceRequest and all associated sub-resources. Returns 204 on success.",
    responses={**_ERR_NOT_FOUND},
)
async def delete_service_request(
    service_request_id: int = Path(..., ge=1, description="Public service_request identifier."),
    _existing: ServiceRequestModel = Depends(resolve_service_request),
    service_request_service: ServiceRequestService = Depends(get_service_request_service),
):
    logger.info("Delete a ServiceRequest resource", extra={"event": "route.delete_service_request", "service_request_id": service_request_id})
    await service_request_service.delete_service_request(service_request_id)

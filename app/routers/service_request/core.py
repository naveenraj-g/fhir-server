from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.service_request import get_service_request_service
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
        "Accepts the full nested payload atomically in one DB transaction. `tenant_id`/"
        "`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — an "
        "org-less token is rejected outright (403). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_service_request(
    payload: ServiceRequestCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("service_request", "create")),
    service_request_service: ServiceRequestService = Depends(get_service_request_service),
):
    logger.info("Create a new ServiceRequest resource", extra={"event": "route.create_service_request"})
    log_payload(logger, "service_request.create.payload", payload)
    service_request = await service_request_service.create_service_request(
        payload, actor.org_id, actor.sub
    )
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
    summary="List ServiceRequest resources owned by the authenticated end-user",
    description=(
        "Same filters as `GET /`, always additionally scoped to the authenticated "
        "end-user's own `user_id`, on top of the caller's own org (from the verified "
        "token). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_my_service_requests(
    request: Request,
    actor: AuthUser = Depends(require_permission("service_request", "read")),
    service_request_status: ServiceRequestStatus | None = Query(
        None, alias="status", description="draft | active | on-hold | revoked | completed | entered-in-error | unknown."
    ),
    intent: ServiceRequestIntent | None = Query(None, description="proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option."),
    subject: str | None = Query(None, description="Exact match on the subject reference string."),
    identifier: str | None = Query(None, description="Exact match on the business identifier value."),
    params: ListParams = Depends(),
    service_request_service: ServiceRequestService = Depends(get_service_request_service),
):
    logger.info("List ServiceRequest resources owned by the authenticated end-user", extra={"event": "route.list_my_service_requests"})
    items, total = await service_request_service.get_me(
        user_id=actor.sub, org_id=actor.org_id, status=service_request_status, intent=intent,
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
        "Scoped to the caller's own org — get_service_request_scoped() raises "
        "PermissionDeniedError (403) outright for an org-less token, or NotFoundError "
        "(404, never 403) if it belongs to a different org, so existence isn't leaked. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_service_request(
    request: Request,
    service_request_id: int = Path(..., ge=1, description="Public service_request identifier."),
    actor: AuthUser = Depends(require_permission("service_request", "read")),
    service_request_service: ServiceRequestService = Depends(get_service_request_service),
):
    logger.info(
        "Retrieve a ServiceRequest resource by public service_request_id",
        extra={"event": "route.get_service_request_by_id", "service_request_id": service_request_id},
    )
    service_request = await service_request_service.get_service_request_scoped(
        service_request_id, actor.org_id
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
        "omitted lists are left untouched. Scoped to the caller's own org — "
        "patch_service_request() raises NotFoundError (404, not 403) if actor.org_id "
        "doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_service_request(
    payload: ServiceRequestPatchSchema,
    request: Request,
    service_request_id: int = Path(..., ge=1, description="Public service_request identifier."),
    actor: AuthUser = Depends(require_permission("service_request", "update")),
    service_request_service: ServiceRequestService = Depends(get_service_request_service),
):
    logger.info("Update a ServiceRequest resource", extra={"event": "route.patch_service_request", "service_request_id": service_request_id})
    log_payload(logger, "service_request.patch.payload", payload)
    updated = await service_request_service.patch_service_request(
        service_request_id, payload, actor.sub, org_id=actor.org_id
    )
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
        "identifier value). Always scoped to the caller's own org (from the verified "
        "token) — `org_id` is not a client-suppliable filter. Sort with `sort` (e.g. "
        "`-authored_on`); set `total_mode=none` to skip the COUNT(*) on large result "
        "sets. " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_service_requests(
    request: Request,
    actor: AuthUser = Depends(require_permission("service_request", "read")),
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
        org_id=actor.org_id, status=service_request_status, intent=intent,
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
    description=(
        "Permanently deletes the ServiceRequest and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the "
        "resource exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_service_request(
    service_request_id: int = Path(..., ge=1, description="Public service_request identifier."),
    actor: AuthUser = Depends(require_permission("service_request", "delete")),
    service_request_service: ServiceRequestService = Depends(get_service_request_service),
):
    logger.info("Delete a ServiceRequest resource", extra={"event": "route.delete_service_request", "service_request_id": service_request_id})
    await service_request_service.delete_service_request(service_request_id, org_id=actor.org_id)

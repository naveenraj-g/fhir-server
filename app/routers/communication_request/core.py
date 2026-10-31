from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import (
    format_paginated_response,
    format_response,
)
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.communication_request import get_communication_request_service
from app.schemas.communication_request import (
    CommunicationRequestCreateSchema,
    CommunicationRequestPatchSchema,
)
from app.services.communication_request import CommunicationRequestService

from ._responses import (
    _CONTENT_NEG,
    _ERR_NOT_FOUND,
    _ERR_VALIDATION,
    _LIST_200,
    _SINGLE_200,
    _SINGLE_201,
)

router = APIRouter()

logger = get_logger(__name__)


# ── Create ─────────────────────────────────────────────────────────────────────


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    operation_id="create_communication_request",
    summary="Create a new CommunicationRequest resource",
    description=(
        "A request to convey information; e.g. the alert, notification, or request to make a phone call. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) "
        "— an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_communication_request(
    payload: CommunicationRequestCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("communication_request", "create")),
    communication_request_service: CommunicationRequestService = Depends(
        get_communication_request_service
    ),
):
    logger.info(
        "Create a new CommunicationRequest resource",
        extra={"event": "route.create_communication_request"},
    )
    log_payload(logger, "communication_request.create.payload", payload)
    model = await communication_request_service.create_communication_request(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        communication_request_service._to_fhir(model),
        communication_request_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{communication_request_id}",
    operation_id="get_communication_request",
    summary="Get a CommunicationRequest resource by ID",
    description=(
        "Returns the full CommunicationRequest resource with all sub-resources populated. "
        "Scoped to the caller's own org — returns 404 (never 403) if the resource belongs "
        "to a different org, to avoid leaking existence. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_communication_request(
    request: Request,
    communication_request_id: int = Path(
        ..., ge=1, description="Public CommunicationRequest identifier."
    ),
    actor: AuthUser = Depends(require_permission("communication_request", "read")),
    communication_request_service: CommunicationRequestService = Depends(
        get_communication_request_service
    ),
):
    logger.info(
        "Get a CommunicationRequest resource by ID",
        extra={
            "event": "route.get_communication_request",
            "communication_request_id": communication_request_id,
        },
    )
    model = await communication_request_service.get_communication_request_scoped(
        communication_request_id, actor.org_id
    )
    return format_response(
        communication_request_service._to_fhir(model),
        communication_request_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{communication_request_id}",
    operation_id="patch_communication_request",
    summary="Update a CommunicationRequest resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_communication_request(
    payload: CommunicationRequestPatchSchema,
    request: Request,
    communication_request_id: int = Path(
        ..., ge=1, description="Public CommunicationRequest identifier."
    ),
    actor: AuthUser = Depends(require_permission("communication_request", "update")),
    communication_request_service: CommunicationRequestService = Depends(
        get_communication_request_service
    ),
):
    logger.info(
        "Update a CommunicationRequest resource",
        extra={
            "event": "route.patch_communication_request",
            "communication_request_id": communication_request_id,
        },
    )
    log_payload(logger, "communication_request.patch.payload", payload)
    updated = await communication_request_service.patch_communication_request(
        communication_request_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        communication_request_service._to_fhir(updated),
        communication_request_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_communication_requests",
    summary="List all CommunicationRequest resources",
    description=(
        "Returns a paginated list of CommunicationRequest resources. Filter by subject, status, priority, etc. "
        "Always scoped to the caller's own org (from the verified token). "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_communication_requests(
    request: Request,
    actor: AuthUser = Depends(require_permission("communication_request", "read")),
    subject: str | None = Query(
        None, description="Focus of message (e.g. 'Patient/10001')."
    ),
    status: str | None = Query(None, description="CommunicationRequest status."),
    priority: str | None = Query(None, description="CommunicationRequest priority."),
    encounter: str | None = Query(
        None, description="Encounter created as part of (e.g. 'Encounter/20001')."
    ),
    requester: str | None = Query(
        None, description="Who asked for notification (e.g. 'Practitioner/30001')."
    ),
    sender: str | None = Query(None, description="Message sender."),
    pagination: ListParams = Depends(),
    communication_request_service: CommunicationRequestService = Depends(
        get_communication_request_service
    ),
):
    logger.info(
        "List all CommunicationRequest resources",
        extra={"event": "route.list_communication_requests"},
    )
    total, items = await communication_request_service.list_communication_requests(
        org_id=actor.org_id,
        subject=subject,
        status=status,
        priority=priority,
        encounter=encounter,
        requester=requester,
        sender=sender,
        limit=pagination.limit,
        offset=pagination.offset,
        sort=pagination.sort,
    )
    return format_paginated_response(
        [communication_request_service._to_fhir(c) for c in items],
        [communication_request_service._to_plain(c) for c in items],
        total,
        pagination.limit,
        pagination.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{communication_request_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_communication_request",
    summary="Delete a CommunicationRequest resource",
    description=(
        "Permanently deletes a CommunicationRequest resource and all its sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={
        204: {"description": "CommunicationRequest deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_communication_request(
    communication_request_id: int = Path(
        ..., ge=1, description="Public CommunicationRequest identifier."
    ),
    actor: AuthUser = Depends(require_permission("communication_request", "delete")),
    communication_request_service: CommunicationRequestService = Depends(
        get_communication_request_service
    ),
):
    logger.info(
        "Delete a CommunicationRequest resource",
        extra={
            "event": "route.delete_communication_request",
            "communication_request_id": communication_request_id,
        },
    )
    await communication_request_service.delete_communication_request(
        communication_request_id, org_id=actor.org_id
    )

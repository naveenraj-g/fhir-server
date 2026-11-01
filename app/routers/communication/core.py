from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import (
    format_paginated_response,
    format_response,
)
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.communication import get_communication_service
from app.schemas.communication import (
    CommunicationCreateSchema,
    CommunicationPatchSchema,
)
from app.services.communication import CommunicationService

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
    operation_id="create_communication",
    summary="Create a new Communication resource",
    description=(
        "An occurrence of information being transmitted; e.g. an alert that was sent to a "
        "responsible provider, a public health agency that was notified about a reportable condition. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) "
        "— an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_communication(
    payload: CommunicationCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("communication", "create")),
    communication_service: CommunicationService = Depends(
        get_communication_service
    ),
):
    logger.info(
        "Create a new Communication resource",
        extra={"event": "route.create_communication"},
    )
    log_payload(logger, "communication.create.payload", payload)
    model = await communication_service.create_communication(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        communication_service._to_fhir(model),
        communication_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{communication_id}",
    operation_id="get_communication",
    summary="Get a Communication resource by ID",
    description=(
        "Returns the full Communication resource with all sub-resources populated. "
        "Scoped to the caller's own org — returns 404 (never 403) if the resource belongs "
        "to a different org, to avoid leaking existence. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_communication(
    request: Request,
    communication_id: int = Path(
        ..., ge=1, description="Public Communication identifier."
    ),
    actor: AuthUser = Depends(require_permission("communication", "read")),
    communication_service: CommunicationService = Depends(
        get_communication_service
    ),
):
    logger.info(
        "Get a Communication resource by ID",
        extra={
            "event": "route.get_communication",
            "communication_id": communication_id,
        },
    )
    model = await communication_service.get_communication_scoped(
        communication_id, actor.org_id
    )
    return format_response(
        communication_service._to_fhir(model),
        communication_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{communication_id}",
    operation_id="patch_communication",
    summary="Update a Communication resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_communication(
    payload: CommunicationPatchSchema,
    request: Request,
    communication_id: int = Path(
        ..., ge=1, description="Public Communication identifier."
    ),
    actor: AuthUser = Depends(require_permission("communication", "update")),
    communication_service: CommunicationService = Depends(
        get_communication_service
    ),
):
    logger.info(
        "Update a Communication resource",
        extra={
            "event": "route.patch_communication",
            "communication_id": communication_id,
        },
    )
    log_payload(logger, "communication.patch.payload", payload)
    updated = await communication_service.patch_communication(
        communication_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        communication_service._to_fhir(updated),
        communication_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_communications",
    summary="List all Communication resources",
    description=(
        "Returns a paginated list of Communication resources. Filter by subject, status, priority, etc. "
        "Always scoped to the caller's own org (from the verified token). "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_communications(
    request: Request,
    actor: AuthUser = Depends(require_permission("communication", "read")),
    subject: str | None = Query(
        None, description="Focus of message (e.g. 'Patient/10001')."
    ),
    communication_status: str | None = Query(
        None, alias="status", description="Communication status."
    ),
    priority: str | None = Query(None, description="Communication priority."),
    encounter: str | None = Query(
        None, description="Encounter created as part of (e.g. 'Encounter/20001')."
    ),
    sender: str | None = Query(None, description="Message sender."),
    recipient: str | None = Query(None, description="Message recipient."),
    pagination: ListParams = Depends(),
    communication_service: CommunicationService = Depends(
        get_communication_service
    ),
):
    logger.info(
        "List all Communication resources",
        extra={"event": "route.list_communications"},
    )
    total, items = await communication_service.list_communications(
        org_id=actor.org_id,
        subject=subject,
        status=communication_status,
        priority=priority,
        encounter=encounter,
        sender=sender,
        recipient=recipient,
        limit=pagination.limit,
        offset=pagination.offset,
        sort=pagination.sort,
    )
    return format_paginated_response(
        [communication_service._to_fhir(c) for c in items],
        [communication_service._to_plain(c) for c in items],
        total,
        pagination.limit,
        pagination.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{communication_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_communication",
    summary="Delete a Communication resource",
    description=(
        "Permanently deletes a Communication resource and all its sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={
        204: {"description": "Communication deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_communication(
    communication_id: int = Path(
        ..., ge=1, description="Public Communication identifier."
    ),
    actor: AuthUser = Depends(require_permission("communication", "delete")),
    communication_service: CommunicationService = Depends(
        get_communication_service
    ),
):
    logger.info(
        "Delete a Communication resource",
        extra={
            "event": "route.delete_communication",
            "communication_id": communication_id,
        },
    )
    await communication_service.delete_communication(
        communication_id, org_id=actor.org_id
    )

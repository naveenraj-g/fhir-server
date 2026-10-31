from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import (
    format_paginated_response,
    format_response,
)
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.task import get_task_service
from app.schemas.task import (
    TaskCreateSchema,
    TaskPatchSchema,
)
from app.services.task import TaskService

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
    operation_id="create_task",
    summary="Create a new Task resource",
    description=(
        "A task to be performed. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) "
        "— an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_task(
    payload: TaskCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("task", "create")),
    task_service: TaskService = Depends(get_task_service),
):
    logger.info(
        "Create a new Task resource",
        extra={"event": "route.create_task"},
    )
    log_payload(logger, "task.create.payload", payload)
    model = await task_service.create_task(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        task_service._to_fhir(model),
        task_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{task_id}",
    operation_id="get_task",
    summary="Get a Task resource by ID",
    description=(
        "Returns the full Task resource with all sub-resources populated. "
        "Scoped to the caller's own org — returns 404 (never 403) if the resource belongs "
        "to a different org, to avoid leaking existence. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_task(
    request: Request,
    task_id: int = Path(..., ge=1, description="Public Task identifier."),
    actor: AuthUser = Depends(require_permission("task", "read")),
    task_service: TaskService = Depends(get_task_service),
):
    logger.info(
        "Get a Task resource by ID",
        extra={
            "event": "route.get_task",
            "task_id": task_id,
        },
    )
    model = await task_service.get_task_scoped(
        task_id, actor.org_id
    )
    return format_response(
        task_service._to_fhir(model),
        task_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{task_id}",
    operation_id="patch_task",
    summary="Update a Task resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_task(
    payload: TaskPatchSchema,
    request: Request,
    task_id: int = Path(..., ge=1, description="Public Task identifier."),
    actor: AuthUser = Depends(require_permission("task", "update")),
    task_service: TaskService = Depends(get_task_service),
):
    logger.info(
        "Update a Task resource",
        extra={
            "event": "route.patch_task",
            "task_id": task_id,
        },
    )
    log_payload(logger, "task.patch.payload", payload)
    updated = await task_service.patch_task(
        task_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        task_service._to_fhir(updated),
        task_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_tasks",
    summary="List all Task resources",
    description=(
        "Returns a paginated list of Task resources. Filter by status, intent, "
        "priority, focus, for, owner, requester, encounter. "
        "Always scoped to the caller's own org (from the verified token). "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_tasks(
    request: Request,
    actor: AuthUser = Depends(require_permission("task", "read")),
    status_filter: str | None = Query(
        None, alias="status", description="Task status."
    ),
    intent: str | None = Query(
        None, description="Task intent."
    ),
    priority: str | None = Query(
        None, description="Task priority."
    ),
    focus: str | None = Query(
        None, description="What task is acting on."
    ),
    for_: str | None = Query(
        None, alias="for", description="Beneficiary of the task."
    ),
    owner: str | None = Query(
        None, description="Responsible individual."
    ),
    requester: str | None = Query(
        None, description="Who is asking for task to be done."
    ),
    encounter: str | None = Query(
        None, description="Healthcare event during which task was created."
    ),
    pagination: ListParams = Depends(),
    task_service: TaskService = Depends(get_task_service),
):
    logger.info("List all Task resources", extra={"event": "route.list_tasks"})
    total, items = await task_service.list_tasks(
        org_id=actor.org_id,
        status=status_filter,
        intent=intent,
        priority=priority,
        focus=focus,
        for_=for_,
        owner=owner,
        requester=requester,
        encounter=encounter,
        limit=pagination.limit,
        offset=pagination.offset,
        sort=pagination.sort,
    )
    return format_paginated_response(
        [task_service._to_fhir(t) for t in items],
        [task_service._to_plain(t) for t in items],
        total,
        pagination.limit,
        pagination.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_task",
    summary="Delete a Task resource",
    description=(
        "Permanently deletes a Task resource and all its sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={
        204: {"description": "Task deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_task(
    task_id: int = Path(..., ge=1, description="Public Task identifier."),
    actor: AuthUser = Depends(require_permission("task", "delete")),
    task_service: TaskService = Depends(get_task_service),
):
    logger.info(
        "Delete a Task resource",
        extra={
            "event": "route.delete_task",
            "task_id": task_id,
        },
    )
    await task_service.delete_task(task_id, org_id=actor.org_id)

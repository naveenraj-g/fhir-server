from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import (
    format_paginated_response,
    format_response,
)
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.goal import get_goal_service
from app.schemas.goal import (
    GoalCreateSchema,
    GoalPatchSchema,
)
from app.services.goal import GoalService

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
    operation_id="create_goal",
    summary="Create a new Goal resource",
    description=(
        "Describes the intended objective(s) for a patient, group or organization. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) "
        "— an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_goal(
    payload: GoalCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("goal", "create")),
    goal_service: GoalService = Depends(get_goal_service),
):
    logger.info(
        "Create a new Goal resource",
        extra={"event": "route.create_goal"},
    )
    log_payload(logger, "goal.create.payload", payload)
    model = await goal_service.create_goal(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        goal_service._to_fhir(model),
        goal_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{goal_id}",
    operation_id="get_goal",
    summary="Get a Goal resource by ID",
    description=(
        "Returns the full Goal resource with all sub-resources populated. "
        "Scoped to the caller's own org — returns 404 (never 403) if the resource belongs "
        "to a different org, to avoid leaking existence. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_goal(
    request: Request,
    goal_id: int = Path(..., ge=1, description="Public Goal identifier."),
    actor: AuthUser = Depends(require_permission("goal", "read")),
    goal_service: GoalService = Depends(get_goal_service),
):
    logger.info(
        "Get a Goal resource by ID",
        extra={
            "event": "route.get_goal",
            "goal_id": goal_id,
        },
    )
    model = await goal_service.get_goal_scoped(
        goal_id, actor.org_id
    )
    return format_response(
        goal_service._to_fhir(model),
        goal_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{goal_id}",
    operation_id="patch_goal",
    summary="Update a Goal resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_goal(
    payload: GoalPatchSchema,
    request: Request,
    goal_id: int = Path(..., ge=1, description="Public Goal identifier."),
    actor: AuthUser = Depends(require_permission("goal", "update")),
    goal_service: GoalService = Depends(get_goal_service),
):
    logger.info(
        "Update a Goal resource",
        extra={
            "event": "route.patch_goal",
            "goal_id": goal_id,
        },
    )
    log_payload(logger, "goal.patch.payload", payload)
    updated = await goal_service.patch_goal(
        goal_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        goal_service._to_fhir(updated),
        goal_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_goals",
    summary="List all Goal resources",
    description=(
        "Returns a paginated list of Goal resources. Filter by subject, lifecycle_status. "
        "Always scoped to the caller's own org (from the verified token). "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_goals(
    request: Request,
    actor: AuthUser = Depends(require_permission("goal", "read")),
    subject: str | None = Query(
        None, description="Who this goal is intended for (e.g. 'Patient/10001')."
    ),
    lifecycle_status: str | None = Query(
        None, alias="lifecycle-status", description="Goal lifecycle status."
    ),
    pagination: ListParams = Depends(),
    goal_service: GoalService = Depends(get_goal_service),
):
    logger.info("List all Goal resources", extra={"event": "route.list_goals"})
    total, items = await goal_service.list_goals(
        org_id=actor.org_id,
        subject=subject,
        lifecycle_status=lifecycle_status,
        limit=pagination.limit,
        offset=pagination.offset,
        sort=pagination.sort,
    )
    return format_paginated_response(
        [goal_service._to_fhir(g) for g in items],
        [goal_service._to_plain(g) for g in items],
        total,
        pagination.limit,
        pagination.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_goal",
    summary="Delete a Goal resource",
    description=(
        "Permanently deletes a Goal resource and all its sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={
        204: {"description": "Goal deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_goal(
    goal_id: int = Path(..., ge=1, description="Public Goal identifier."),
    actor: AuthUser = Depends(require_permission("goal", "delete")),
    goal_service: GoalService = Depends(get_goal_service),
):
    logger.info(
        "Delete a Goal resource",
        extra={
            "event": "route.delete_goal",
            "goal_id": goal_id,
        },
    )
    await goal_service.delete_goal(goal_id, org_id=actor.org_id)

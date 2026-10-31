from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import (
    format_paginated_response,
    format_response,
)
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.flag import get_flag_service
from app.schemas.flag import (
    FlagCreateSchema,
    FlagPatchSchema,
)
from app.services.flag import FlagService

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
    operation_id="create_flag",
    summary="Create a new Flag resource",
    description=(
        "Prospective warnings of potential issues when providing care to the patient. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) "
        "— an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_flag(
    payload: FlagCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("flag", "create")),
    flag_service: FlagService = Depends(get_flag_service),
):
    logger.info(
        "Create a new Flag resource",
        extra={"event": "route.create_flag"},
    )
    log_payload(logger, "flag.create.payload", payload)
    model = await flag_service.create_flag(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        flag_service._to_fhir(model),
        flag_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{flag_id}",
    operation_id="get_flag",
    summary="Get a Flag resource by ID",
    description=(
        "Returns the full Flag resource with all sub-resources populated. "
        "Scoped to the caller's own org — returns 404 (never 403) if the resource belongs "
        "to a different org, to avoid leaking existence. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_flag(
    request: Request,
    flag_id: int = Path(..., ge=1, description="Public Flag identifier."),
    actor: AuthUser = Depends(require_permission("flag", "read")),
    flag_service: FlagService = Depends(get_flag_service),
):
    logger.info(
        "Get a Flag resource by ID",
        extra={
            "event": "route.get_flag",
            "flag_id": flag_id,
        },
    )
    model = await flag_service.get_flag_scoped(
        flag_id, actor.org_id
    )
    return format_response(
        flag_service._to_fhir(model),
        flag_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{flag_id}",
    operation_id="patch_flag",
    summary="Update a Flag resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_flag(
    payload: FlagPatchSchema,
    request: Request,
    flag_id: int = Path(..., ge=1, description="Public Flag identifier."),
    actor: AuthUser = Depends(require_permission("flag", "update")),
    flag_service: FlagService = Depends(get_flag_service),
):
    logger.info(
        "Update a Flag resource",
        extra={
            "event": "route.patch_flag",
            "flag_id": flag_id,
        },
    )
    log_payload(logger, "flag.patch.payload", payload)
    updated = await flag_service.patch_flag(
        flag_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        flag_service._to_fhir(updated),
        flag_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_flags",
    summary="List all Flag resources",
    description=(
        "Returns a paginated list of Flag resources. Filter by subject, status, "
        "encounter, author. "
        "Always scoped to the caller's own org (from the verified token). "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_flags(
    request: Request,
    actor: AuthUser = Depends(require_permission("flag", "read")),
    subject: str | None = Query(
        None, description="The identity of a subject to list flags for."
    ),
    flag_status: str | None = Query(
        None, alias="status", description="active | inactive | entered-in-error."
    ),
    encounter: str | None = Query(
        None, description="Alert relevant to encounter."
    ),
    author: str | None = Query(
        None, description="Flag creator."
    ),
    pagination: ListParams = Depends(),
    flag_service: FlagService = Depends(get_flag_service),
):
    logger.info("List all Flag resources", extra={"event": "route.list_flags"})
    total, items = await flag_service.list_flags(
        org_id=actor.org_id,
        subject=subject,
        status=flag_status,
        encounter=encounter,
        author=author,
        limit=pagination.limit,
        offset=pagination.offset,
        sort=pagination.sort,
    )
    return format_paginated_response(
        [flag_service._to_fhir(f) for f in items],
        [flag_service._to_plain(f) for f in items],
        total,
        pagination.limit,
        pagination.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{flag_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_flag",
    summary="Delete a Flag resource",
    description=(
        "Permanently deletes a Flag resource and all its sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={
        204: {"description": "Flag deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_flag(
    flag_id: int = Path(..., ge=1, description="Public Flag identifier."),
    actor: AuthUser = Depends(require_permission("flag", "delete")),
    flag_service: FlagService = Depends(get_flag_service),
):
    logger.info(
        "Delete a Flag resource",
        extra={
            "event": "route.delete_flag",
            "flag_id": flag_id,
        },
    )
    await flag_service.delete_flag(flag_id, org_id=actor.org_id)

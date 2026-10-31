from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.activity_definition import (
    get_activity_definition_service,
)
from app.schemas.activity_definition import (
    ActivityDefinitionCreateSchema,
    ActivityDefinitionPatchSchema,
)
from app.services.activity_definition import ActivityDefinitionService

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
    operation_id="create_activity_definition",
    summary="Create a new ActivityDefinition resource",
    description=(
        "Defines an activity to be performed (order, procedure, medication, etc.). "
        "Accepts the full nested payload atomically in one DB transaction. `tenant_id`/"
        "`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — an "
        "org-less token is rejected outright (403). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_activity_definition(
    payload: ActivityDefinitionCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("activity_definition", "create")),
    activity_definition_service: ActivityDefinitionService = Depends(
        get_activity_definition_service
    ),
):
    logger.info(
        "Create a new ActivityDefinition resource",
        extra={"event": "route.create_activity_definition"},
    )
    log_payload(logger, "activity_definition.create.payload", payload)
    ad = await activity_definition_service.create_activity_definition(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        activity_definition_service._to_fhir(ad),
        activity_definition_service._to_plain(ad),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{activity_definition_id}",
    operation_id="get_activity_definition",
    summary="Get an ActivityDefinition resource by ID",
    description=(
        "Returns the full ActivityDefinition resource with all sub-resources populated. "
        "Scoped to the caller's own org — returns 404 (never 403) if the resource belongs "
        "to a different org, to avoid leaking existence. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_activity_definition(
    request: Request,
    activity_definition_id: int = Path(
        ..., ge=1, description="Public activity_definition identifier."
    ),
    actor: AuthUser = Depends(require_permission("activity_definition", "read")),
    activity_definition_service: ActivityDefinitionService = Depends(
        get_activity_definition_service
    ),
):
    logger.info(
        "Get an ActivityDefinition resource by ID",
        extra={
            "event": "route.get_activity_definition",
            "activity_definition_id": activity_definition_id,
        },
    )
    ad = await activity_definition_service.get_activity_definition_scoped(
        activity_definition_id, actor.org_id
    )
    return format_response(
        activity_definition_service._to_fhir(ad),
        activity_definition_service._to_plain(ad),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{activity_definition_id}",
    operation_id="patch_activity_definition",
    summary="Update an ActivityDefinition resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_activity_definition(
    payload: ActivityDefinitionPatchSchema,
    request: Request,
    activity_definition_id: int = Path(
        ..., ge=1, description="Public activity_definition identifier."
    ),
    actor: AuthUser = Depends(require_permission("activity_definition", "update")),
    activity_definition_service: ActivityDefinitionService = Depends(
        get_activity_definition_service
    ),
):
    logger.info(
        "Update an ActivityDefinition resource",
        extra={
            "event": "route.patch_activity_definition",
            "activity_definition_id": activity_definition_id,
        },
    )
    log_payload(logger, "activity_definition.patch.payload", payload)
    updated = await activity_definition_service.patch_activity_definition(
        activity_definition_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        activity_definition_service._to_fhir(updated),
        activity_definition_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_activity_definitions",
    summary="List all ActivityDefinition resources",
    description=(
        "Returns a paginated list of ActivityDefinition resources. Filter by name, "
        "title, status, kind, intent, priority, identifier. "
        "Always scoped to the caller's own org (from the verified token). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_activity_definitions(
    request: Request,
    actor: AuthUser = Depends(require_permission("activity_definition", "read")),
    name: str | None = Query(None, description="ActivityDefinition name."),
    title: str | None = Query(None, description="ActivityDefinition title."),
    status: str | None = Query(None, description="ActivityDefinition status."),
    kind: str | None = Query(None, description="ActivityDefinition kind."),
    intent: str | None = Query(None, description="ActivityDefinition intent."),
    priority: str | None = Query(None, description="ActivityDefinition priority."),
    identifier: str | None = Query(None, description="Business identifier value."),
    list_params: ListParams = Depends(),
    activity_definition_service: ActivityDefinitionService = Depends(
        get_activity_definition_service
    ),
):
    logger.info(
        "List ActivityDefinition resources",
        extra={"event": "route.list_activity_definitions", "org_id": actor.org_id},
    )
    ads, total = await activity_definition_service.list_activity_definitions(
        org_id=actor.org_id,
        name=name,
        title=title,
        status=status,
        kind=kind,
        intent=intent,
        priority=priority,
        identifier=identifier,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
        total_mode=list_params.total_mode,
    )
    return format_paginated_response(
        [activity_definition_service._to_fhir(a) for a in ads],
        [activity_definition_service._to_plain(a) for a in ads],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{activity_definition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_activity_definition",
    summary="Delete an ActivityDefinition resource",
    description=(
        "Permanently deletes the ActivityDefinition and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the resource "
        "exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_activity_definition(
    activity_definition_id: int = Path(
        ..., ge=1, description="Public activity_definition identifier."
    ),
    actor: AuthUser = Depends(require_permission("activity_definition", "delete")),
    activity_definition_service: ActivityDefinitionService = Depends(
        get_activity_definition_service
    ),
):
    logger.info(
        "Delete an ActivityDefinition resource",
        extra={
            "event": "route.delete_activity_definition",
            "activity_definition_id": activity_definition_id,
        },
    )
    await activity_definition_service.delete_activity_definition(
        activity_definition_id, org_id=actor.org_id
    )

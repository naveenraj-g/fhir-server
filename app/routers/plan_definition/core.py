from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.plan_definition import (
    get_plan_definition_service,
)
from app.schemas.plan_definition import (
    PlanDefinitionCreateSchema,
    PlanDefinitionPatchSchema,
)
from app.services.plan_definition import PlanDefinitionService

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
    operation_id="create_plan_definition",
    summary="Create a new PlanDefinition resource",
    description=(
        "Defines a pre-defined group of actions to be taken (order sets, protocols, CDS rules). "
        "Accepts the full nested payload atomically in one DB transaction. `tenant_id`/"
        "`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — an "
        "org-less token is rejected outright (403). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_plan_definition(
    payload: PlanDefinitionCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("plan_definition", "create")),
    plan_definition_service: PlanDefinitionService = Depends(
        get_plan_definition_service
    ),
):
    logger.info(
        "Create a new PlanDefinition resource",
        extra={"event": "route.create_plan_definition"},
    )
    log_payload(logger, "plan_definition.create.payload", payload)
    pd = await plan_definition_service.create_plan_definition(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        plan_definition_service._to_fhir(pd),
        plan_definition_service._to_plain(pd),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{plan_definition_id}",
    operation_id="get_plan_definition",
    summary="Get a PlanDefinition resource by ID",
    description=(
        "Returns the full PlanDefinition resource with all sub-resources and actions populated. "
        "Scoped to the caller's own org — returns 404 (never 403) if the resource belongs "
        "to a different org, to avoid leaking existence. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_plan_definition(
    request: Request,
    plan_definition_id: int = Path(
        ..., ge=1, description="Public plan_definition identifier."
    ),
    actor: AuthUser = Depends(require_permission("plan_definition", "read")),
    plan_definition_service: PlanDefinitionService = Depends(
        get_plan_definition_service
    ),
):
    logger.info(
        "Get a PlanDefinition resource by ID",
        extra={
            "event": "route.get_plan_definition",
            "plan_definition_id": plan_definition_id,
        },
    )
    pd = await plan_definition_service.get_plan_definition_scoped(
        plan_definition_id, actor.org_id
    )
    return format_response(
        plan_definition_service._to_fhir(pd),
        plan_definition_service._to_plain(pd),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{plan_definition_id}",
    operation_id="patch_plan_definition",
    summary="Update a PlanDefinition resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_plan_definition(
    payload: PlanDefinitionPatchSchema,
    request: Request,
    plan_definition_id: int = Path(
        ..., ge=1, description="Public plan_definition identifier."
    ),
    actor: AuthUser = Depends(require_permission("plan_definition", "update")),
    plan_definition_service: PlanDefinitionService = Depends(
        get_plan_definition_service
    ),
):
    logger.info(
        "Update a PlanDefinition resource",
        extra={
            "event": "route.patch_plan_definition",
            "plan_definition_id": plan_definition_id,
        },
    )
    log_payload(logger, "plan_definition.patch.payload", payload)
    updated = await plan_definition_service.patch_plan_definition(
        plan_definition_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        plan_definition_service._to_fhir(updated),
        plan_definition_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_plan_definitions",
    summary="List all PlanDefinition resources",
    description=(
        "Returns a paginated list of PlanDefinition resources. Filter by name, "
        "title, status, url, version, identifier. "
        "Always scoped to the caller's own org (from the verified token). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_plan_definitions(
    request: Request,
    actor: AuthUser = Depends(require_permission("plan_definition", "read")),
    name: str | None = Query(None, description="PlanDefinition name."),
    title: str | None = Query(None, description="PlanDefinition title."),
    status: str | None = Query(None, description="PlanDefinition status."),
    url: str | None = Query(None, description="PlanDefinition canonical URL."),
    version: str | None = Query(None, description="PlanDefinition business version."),
    identifier: str | None = Query(None, description="Business identifier value."),
    list_params: ListParams = Depends(),
    plan_definition_service: PlanDefinitionService = Depends(
        get_plan_definition_service
    ),
):
    logger.info(
        "List PlanDefinition resources",
        extra={"event": "route.list_plan_definitions", "org_id": actor.org_id},
    )
    pds, total = await plan_definition_service.list_plan_definitions(
        org_id=actor.org_id,
        name=name,
        title=title,
        status=status,
        url=url,
        version=version,
        identifier=identifier,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
        total_mode=list_params.total_mode,
    )
    return format_paginated_response(
        [plan_definition_service._to_fhir(p) for p in pds],
        [plan_definition_service._to_plain(p) for p in pds],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{plan_definition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_plan_definition",
    summary="Delete a PlanDefinition resource",
    description=(
        "Permanently deletes the PlanDefinition and all associated sub-resources and actions. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the resource "
        "exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_plan_definition(
    plan_definition_id: int = Path(
        ..., ge=1, description="Public plan_definition identifier."
    ),
    actor: AuthUser = Depends(require_permission("plan_definition", "delete")),
    plan_definition_service: PlanDefinitionService = Depends(
        get_plan_definition_service
    ),
):
    logger.info(
        "Delete a PlanDefinition resource",
        extra={
            "event": "route.delete_plan_definition",
            "plan_definition_id": plan_definition_id,
        },
    )
    await plan_definition_service.delete_plan_definition(
        plan_definition_id, org_id=actor.org_id
    )

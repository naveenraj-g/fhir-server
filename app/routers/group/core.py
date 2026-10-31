from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.group import get_group_service
from app.schemas.group import GroupCreateSchema, GroupPatchSchema
from app.services.group import GroupService

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
    operation_id="create_group",
    summary="Create a new Group resource",
    description=(
        "Represents a defined collection of entities (persons, animals, devices, etc.). "
        "Accepts the full nested payload atomically in one DB transaction. `tenant_id`/"
        "`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — an "
        "org-less token is rejected outright (403). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_group(
    payload: GroupCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("group", "create")),
    group_service: GroupService = Depends(get_group_service),
):
    logger.info(
        "Create a new Group resource",
        extra={"event": "route.create_group"},
    )
    log_payload(logger, "group.create.payload", payload)
    group = await group_service.create_group(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        group_service._to_fhir(group),
        group_service._to_plain(group),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{group_id}",
    operation_id="get_group",
    summary="Get a Group resource by ID",
    description=(
        "Returns the full Group resource with all sub-resources populated. "
        "Scoped to the caller's own org — returns 404 (never 403) if the resource belongs "
        "to a different org, to avoid leaking existence. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_group(
    request: Request,
    group_id: int = Path(
        ..., ge=1, description="Public group identifier."
    ),
    actor: AuthUser = Depends(require_permission("group", "read")),
    group_service: GroupService = Depends(get_group_service),
):
    logger.info(
        "Get a Group resource by ID",
        extra={"event": "route.get_group", "group_id": group_id},
    )
    group = await group_service.get_group_scoped(
        group_id, actor.org_id
    )
    return format_response(
        group_service._to_fhir(group),
        group_service._to_plain(group),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{group_id}",
    operation_id="patch_group",
    summary="Update a Group resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_group(
    payload: GroupPatchSchema,
    request: Request,
    group_id: int = Path(
        ..., ge=1, description="Public group identifier."
    ),
    actor: AuthUser = Depends(require_permission("group", "update")),
    group_service: GroupService = Depends(get_group_service),
):
    logger.info(
        "Update a Group resource",
        extra={
            "event": "route.patch_group",
            "group_id": group_id,
        },
    )
    log_payload(logger, "group.patch.payload", payload)
    updated = await group_service.patch_group(
        group_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        group_service._to_fhir(updated),
        group_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_groups",
    summary="List all Group resources",
    description=(
        "Returns a paginated list of Group resources. Filter by type, actual, "
        "active, name, code, managing_entity, member, characteristic, identifier. "
        "Always scoped to the caller's own org (from the verified token). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_groups(
    request: Request,
    actor: AuthUser = Depends(require_permission("group", "read")),
    type: str | None = Query(
        None, description="person | animal | practitioner | device | medication | substance."
    ),
    actual: bool | None = Query(
        None, description="true for actual specific group, false for definitional."
    ),
    active: bool | None = Query(
        None, description="Whether this group's record is in active use."
    ),
    name: str | None = Query(None, description="Label for Group."),
    code: str | None = Query(None, description="Kind of Group members (matches text or coding.code)."),
    managing_entity: str | None = Query(
        None, description="Managing entity reference (e.g. Organization/190001)."
    ),
    member: str | None = Query(None, description="Member reference (e.g. Patient/10001)."),
    characteristic: str | None = Query(None, description="Characteristic code."),
    characteristic_value: str | None = Query(None, description="Characteristic value."),
    exclude: bool | None = Query(
        None, description="Group includes or excludes members with this characteristic."
    ),
    identifier: str | None = Query(None, description="Business identifier value."),
    list_params: ListParams = Depends(),
    group_service: GroupService = Depends(get_group_service),
):
    logger.info(
        "List Group resources",
        extra={"event": "route.list_groups", "org_id": actor.org_id},
    )
    groups, total = await group_service.list_groups(
        org_id=actor.org_id,
        type=type,
        actual=actual,
        active=active,
        name=name,
        code=code,
        managing_entity=managing_entity,
        member=member,
        characteristic=characteristic,
        characteristic_value=characteristic_value,
        exclude=exclude,
        identifier=identifier,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
        total_mode=list_params.total_mode,
    )
    return format_paginated_response(
        [group_service._to_fhir(g) for g in groups],
        [group_service._to_plain(g) for g in groups],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_group",
    summary="Delete a Group resource",
    description=(
        "Permanently deletes the Group and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the resource "
        "exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_group(
    group_id: int = Path(
        ..., ge=1, description="Public group identifier."
    ),
    actor: AuthUser = Depends(require_permission("group", "delete")),
    group_service: GroupService = Depends(get_group_service),
):
    logger.info(
        "Delete a Group resource",
        extra={
            "event": "route.delete_group",
            "group_id": group_id,
        },
    )
    await group_service.delete_group(
        group_id, org_id=actor.org_id
    )

from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import format_paginated_response, format_response
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.observation_definition import (
    get_observation_definition_service,
)
from app.models.observation_definition import ObservationDefinitionPermittedDataType
from app.schemas.observation_definition import (
    ObservationDefinitionCreateSchema,
    ObservationDefinitionPatchSchema,
)
from app.services.observation_definition import ObservationDefinitionService

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
    operation_id="create_observation_definition",
    summary="Create a new ObservationDefinition resource",
    description=(
        "Set of codes, allowable data types, units, and qualified intervals for a clinical or lab observation. "
        "Accepts the full nested payload atomically in one DB transaction. `tenant_id`/"
        "`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — an "
        "org-less token is rejected outright (403). " + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_observation_definition(
    payload: ObservationDefinitionCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("observation_definition", "create")),
    observation_definition_service: ObservationDefinitionService = Depends(
        get_observation_definition_service
    ),
):
    logger.info(
        "Create a new ObservationDefinition resource",
        extra={"event": "route.create_observation_definition"},
    )
    log_payload(logger, "observation_definition.create.payload", payload)
    od = await observation_definition_service.create_observation_definition(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        observation_definition_service._to_fhir(od),
        observation_definition_service._to_plain(od),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Get by ID ──────────────────────────────────────────────────────────────────


@router.get(
    "/{observation_definition_id}",
    operation_id="get_observation_definition",
    summary="Get an ObservationDefinition resource by ID",
    description=(
        "Returns the full ObservationDefinition resource with all sub-resources populated. "
        "Scoped to the caller's own org — returns 404 (never 403) if the resource belongs "
        "to a different org, to avoid leaking existence. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_observation_definition(
    request: Request,
    observation_definition_id: int = Path(
        ..., ge=1, description="Public observation_definition identifier."
    ),
    actor: AuthUser = Depends(require_permission("observation_definition", "read")),
    observation_definition_service: ObservationDefinitionService = Depends(
        get_observation_definition_service
    ),
):
    logger.info(
        "Get an ObservationDefinition resource by ID",
        extra={
            "event": "route.get_observation_definition",
            "observation_definition_id": observation_definition_id,
        },
    )
    od = await observation_definition_service.get_observation_definition_scoped(
        observation_definition_id, actor.org_id
    )
    return format_response(
        observation_definition_service._to_fhir(od),
        observation_definition_service._to_plain(od),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{observation_definition_id}",
    operation_id="patch_observation_definition",
    summary="Update an ObservationDefinition resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_observation_definition(
    payload: ObservationDefinitionPatchSchema,
    request: Request,
    observation_definition_id: int = Path(
        ..., ge=1, description="Public observation_definition identifier."
    ),
    actor: AuthUser = Depends(require_permission("observation_definition", "update")),
    observation_definition_service: ObservationDefinitionService = Depends(
        get_observation_definition_service
    ),
):
    logger.info(
        "Update an ObservationDefinition resource",
        extra={
            "event": "route.patch_observation_definition",
            "observation_definition_id": observation_definition_id,
        },
    )
    log_payload(logger, "observation_definition.patch.payload", payload)
    updated = await observation_definition_service.patch_observation_definition(
        observation_definition_id, payload, actor.sub, org_id=actor.org_id
    )
    return format_response(
        observation_definition_service._to_fhir(updated),
        observation_definition_service._to_plain(updated),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_observation_definitions",
    summary="List all ObservationDefinition resources",
    description=(
        "Returns a paginated list of ObservationDefinition resources. Filter by code, "
        "category, method, identifier. "
        "Always scoped to the caller's own org (from the verified token). " + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_observation_definitions(
    request: Request,
    actor: AuthUser = Depends(require_permission("observation_definition", "read")),
    code: str | None = Query(None, description="Observation code value."),
    category: str | None = Query(None, description="Category code value."),
    method: str | None = Query(None, description="Method code value."),
    permitted_data_type: ObservationDefinitionPermittedDataType | None = Query(
        None, description="Permitted data type."
    ),
    identifier: str | None = Query(None, description="Business identifier value."),
    list_params: ListParams = Depends(),
    observation_definition_service: ObservationDefinitionService = Depends(
        get_observation_definition_service
    ),
):
    logger.info(
        "List ObservationDefinition resources",
        extra={"event": "route.list_observation_definitions", "org_id": actor.org_id},
    )
    ods, total = await observation_definition_service.list_observation_definitions(
        org_id=actor.org_id,
        code=code,
        category=category,
        method=method,
        identifier=identifier,
        permitted_data_type=permitted_data_type.value if permitted_data_type else None,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
        total_mode=list_params.total_mode,
    )
    return format_paginated_response(
        [observation_definition_service._to_fhir(o) for o in ods],
        [observation_definition_service._to_plain(o) for o in ods],
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{observation_definition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_observation_definition",
    summary="Delete an ObservationDefinition resource",
    description=(
        "Permanently deletes the ObservationDefinition and all associated sub-resources. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if the resource "
        "exists but belongs to a different org. Returns 204 on success."
    ),
    responses={**_ERR_NOT_FOUND},
)
async def delete_observation_definition(
    observation_definition_id: int = Path(
        ..., ge=1, description="Public observation_definition identifier."
    ),
    actor: AuthUser = Depends(require_permission("observation_definition", "delete")),
    observation_definition_service: ObservationDefinitionService = Depends(
        get_observation_definition_service
    ),
):
    logger.info(
        "Delete an ObservationDefinition resource",
        extra={
            "event": "route.delete_observation_definition",
            "observation_definition_id": observation_definition_id,
        },
    )
    await observation_definition_service.delete_observation_definition(
        observation_definition_id, org_id=actor.org_id
    )

from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import (
    format_paginated_response,
    format_response,
)
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.specimen_definition import get_specimen_definition_service
from app.schemas.specimen_definition import (
    SpecimenDefinitionCreateSchema,
    SpecimenDefinitionPatchSchema,
)
from app.services.specimen_definition import SpecimenDefinitionService

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
    operation_id="create_specimen_definition",
    summary="Create a new SpecimenDefinition resource",
    description=(
        "A kind of specimen with associated set of requirements. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — "
        "an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_specimen_definition(
    payload: SpecimenDefinitionCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("specimen_definition", "create")),
    specimen_definition_service: SpecimenDefinitionService = Depends(
        get_specimen_definition_service
    ),
):
    logger.info(
        "Create a new SpecimenDefinition resource",
        extra={"event": "route.create_specimen_definition", "org_id": actor.org_id},
    )
    log_payload(logger, "specimen_definition.create.payload", payload)
    model = await specimen_definition_service.create_specimen_definition(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        specimen_definition_service._to_fhir(model),
        specimen_definition_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{specimen_definition_id}",
    operation_id="get_specimen_definition",
    summary="Get a SpecimenDefinition resource by ID",
    description=(
        "Returns the complete SpecimenDefinition representation. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_specimen_definition(
    request: Request,
    specimen_definition_id: int = Path(
        ..., ge=1, description="Public SpecimenDefinition identifier."
    ),
    actor: AuthUser = Depends(require_permission("specimen_definition", "read")),
    specimen_definition_service: SpecimenDefinitionService = Depends(
        get_specimen_definition_service
    ),
):
    logger.info(
        "Get a SpecimenDefinition resource by ID",
        extra={
            "event": "route.get_specimen_definition",
            "specimen_definition_id": specimen_definition_id,
        },
    )
    model = await specimen_definition_service.get_specimen_definition_scoped(
        specimen_definition_id, actor.org_id
    )
    return format_response(
        specimen_definition_service._to_fhir(model),
        specimen_definition_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{specimen_definition_id}",
    operation_id="patch_specimen_definition",
    summary="Update a SpecimenDefinition resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_specimen_definition(
    payload: SpecimenDefinitionPatchSchema,
    request: Request,
    specimen_definition_id: int = Path(
        ..., ge=1, description="Public SpecimenDefinition identifier."
    ),
    actor: AuthUser = Depends(require_permission("specimen_definition", "update")),
    specimen_definition_service: SpecimenDefinitionService = Depends(
        get_specimen_definition_service
    ),
):
    logger.info(
        "Update a SpecimenDefinition resource",
        extra={
            "event": "route.patch_specimen_definition",
            "specimen_definition_id": specimen_definition_id,
        },
    )
    log_payload(logger, "specimen_definition.patch.payload", payload)
    model = await specimen_definition_service.patch_specimen_definition(
        specimen_definition_id, payload, updated_by=actor.sub, org_id=actor.org_id
    )
    return format_response(
        specimen_definition_service._to_fhir(model),
        specimen_definition_service._to_plain(model),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_specimen_definitions",
    summary="List SpecimenDefinition resources",
    description=(
        "Search and filter SpecimenDefinition resources scoped to the caller's org. "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_specimen_definitions(
    request: Request,
    identifier: str | None = Query(
        None, description="Filter by business identifier system|value."
    ),
    type_collected: str | None = Query(
        None, alias="type", description="Filter by type collected code system|code or code."
    ),
    list_params: ListParams = Depends(),
    actor: AuthUser = Depends(require_permission("specimen_definition", "read")),
    specimen_definition_service: SpecimenDefinitionService = Depends(
        get_specimen_definition_service
    ),
):
    logger.info(
        "List SpecimenDefinition resources",
        extra={"event": "route.list_specimen_definitions", "org_id": actor.org_id},
    )
    rows, total = await specimen_definition_service.list_specimen_definitions(
        org_id=actor.org_id,
        identifier=identifier,
        type_collected=type_collected,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
    )
    fhir_list = [specimen_definition_service._to_fhir(r) for r in rows]
    plain_list = [specimen_definition_service._to_plain(r) for r in rows]
    return format_paginated_response(
        fhir_list,
        plain_list,
        total,
        list_params.limit,
        list_params.offset,
        request,
    )


# ── Delete ─────────────────────────────────────────────────────────────────────


@router.delete(
    "/{specimen_definition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_specimen_definition",
    summary="Delete a SpecimenDefinition resource",
    description=(
        "Deletes a SpecimenDefinition and cascades to all child records. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match."
    ),
    responses={
        204: {"description": "SpecimenDefinition deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_specimen_definition(
    specimen_definition_id: int = Path(
        ..., ge=1, description="Public SpecimenDefinition identifier."
    ),
    actor: AuthUser = Depends(require_permission("specimen_definition", "delete")),
    specimen_definition_service: SpecimenDefinitionService = Depends(
        get_specimen_definition_service
    ),
):
    logger.info(
        "Delete a SpecimenDefinition resource",
        extra={
            "event": "route.delete_specimen_definition",
            "specimen_definition_id": specimen_definition_id,
        },
    )
    await specimen_definition_service.delete_specimen_definition(
        specimen_definition_id, org_id=actor.org_id
    )
    return None

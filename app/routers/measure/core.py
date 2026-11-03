from fastapi import APIRouter, Depends, Path, Query, Request, status

from app.auth.models import AuthUser
from app.auth.rbac import require_permission
from app.core.content_negotiation import (
    format_paginated_response,
    format_response,
)
from app.core.logging import get_logger, log_payload
from app.core.pagination import ListParams
from app.di.dependencies.measure import get_measure_service
from app.schemas.measure import (
    MeasureCreateSchema,
    MeasurePatchSchema,
)
from app.services.measure import MeasureService

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
    operation_id="create_measure",
    summary="Create a new Measure resource",
    description=(
        "A quality measure or clinical quality measure definition. "
        "Accepts the full nested payload atomically in one DB transaction. "
        "`tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) — "
        "an org-less token is rejected outright (403). "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_201, **_ERR_VALIDATION},
)
async def create_measure(
    payload: MeasureCreateSchema,
    request: Request,
    actor: AuthUser = Depends(require_permission("measure", "create")),
    measure_service: MeasureService = Depends(get_measure_service),
):
    logger.info(
        "Create a new Measure resource",
        extra={"event": "route.create_measure", "org_id": actor.org_id},
    )
    log_payload(logger, "measure.create.payload", payload)
    model = await measure_service.create_measure(
        payload, actor.org_id, actor.sub
    )
    return format_response(
        measure_service._to_fhir(model),
        measure_service._to_plain(model),
        request,
        status_code=status.HTTP_201_CREATED,
    )


# ── Read ───────────────────────────────────────────────────────────────────────


@router.get(
    "/{measure_id}",
    operation_id="get_measure",
    summary="Get a Measure resource by ID",
    description=(
        "Returns the complete Measure representation. Scoped to the caller's "
        "own org — raises NotFoundError (404, not 403) if actor.org_id doesn't match. "
        + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND},
)
async def get_measure(
    request: Request,
    measure_id: int = Path(
        ..., ge=1, description="Public Measure identifier."
    ),
    actor: AuthUser = Depends(require_permission("measure", "read")),
    measure_service: MeasureService = Depends(get_measure_service),
):
    logger.info(
        "Get a Measure resource by ID",
        extra={
            "event": "route.get_measure",
            "measure_id": measure_id,
        },
    )
    model = await measure_service.get_measure_scoped(
        measure_id, actor.org_id
    )
    return format_response(
        measure_service._to_fhir(model),
        measure_service._to_plain(model),
        request,
    )


# ── Patch ──────────────────────────────────────────────────────────────────────


@router.patch(
    "/{measure_id}",
    operation_id="patch_measure",
    summary="Update a Measure resource",
    description=(
        "Only supplied fields are written; omitted fields are left unchanged. Every "
        "supplied sub-resource list atomically replaces corresponding rows. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match. " + _CONTENT_NEG
    ),
    responses={**_SINGLE_200, **_ERR_NOT_FOUND, **_ERR_VALIDATION},
)
async def patch_measure(
    payload: MeasurePatchSchema,
    request: Request,
    measure_id: int = Path(
        ..., ge=1, description="Public Measure identifier."
    ),
    actor: AuthUser = Depends(require_permission("measure", "update")),
    measure_service: MeasureService = Depends(get_measure_service),
):
    logger.info(
        "Update a Measure resource",
        extra={
            "event": "route.patch_measure",
            "measure_id": measure_id,
        },
    )
    log_payload(logger, "measure.patch.payload", payload)
    model = await measure_service.patch_measure(
        measure_id, payload, updated_by=actor.sub, org_id=actor.org_id
    )
    return format_response(
        measure_service._to_fhir(model),
        measure_service._to_plain(model),
        request,
    )


# ── List ───────────────────────────────────────────────────────────────────────


@router.get(
    "/",
    operation_id="list_measures",
    summary="List Measure resources",
    description=(
        "Search and filter Measure resources scoped to the caller's org. "
        + _CONTENT_NEG
    ),
    responses={**_LIST_200},
)
async def list_measures(
    request: Request,
    url: str | None = Query(None, description="Filter by canonical URL."),
    identifier: str | None = Query(
        None, description="Filter by business identifier system|value or value."
    ),
    name: str | None = Query(None, description="Filter by computer-friendly name."),
    title: str | None = Query(None, description="Filter by human-friendly title."),
    status: str | None = Query(
        None, description="Filter by status (draft, active, retired, unknown)."
    ),
    publisher: str | None = Query(None, description="Filter by publisher."),
    description: str | None = Query(None, description="Filter by description."),
    list_params: ListParams = Depends(),
    actor: AuthUser = Depends(require_permission("measure", "read")),
    measure_service: MeasureService = Depends(get_measure_service),
):
    logger.info(
        "List Measure resources",
        extra={"event": "route.list_measures", "org_id": actor.org_id},
    )
    rows, total = await measure_service.list_measures(
        org_id=actor.org_id,
        url=url,
        identifier=identifier,
        name=name,
        title=title,
        status=status,
        publisher=publisher,
        description=description,
        limit=list_params.limit,
        offset=list_params.offset,
        sort=list_params.sort,
    )
    fhir_list = [measure_service._to_fhir(r) for r in rows]
    plain_list = [measure_service._to_plain(r) for r in rows]
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
    "/{measure_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_measure",
    summary="Delete a Measure resource",
    description=(
        "Deletes a Measure and cascades to all child records. "
        "Scoped to the caller's own org — raises NotFoundError (404, not 403) if "
        "actor.org_id doesn't match."
    ),
    responses={
        204: {"description": "Measure deleted successfully"},
        **_ERR_NOT_FOUND,
    },
)
async def delete_measure(
    measure_id: int = Path(
        ..., ge=1, description="Public Measure identifier."
    ),
    actor: AuthUser = Depends(require_permission("measure", "delete")),
    measure_service: MeasureService = Depends(get_measure_service),
):
    logger.info(
        "Delete a Measure resource",
        extra={
            "event": "route.delete_measure",
            "measure_id": measure_id,
        },
    )
    await measure_service.delete_measure(measure_id, org_id=actor.org_id)
    return None
